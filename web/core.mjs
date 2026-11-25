import { NetCDFReader } from './netcdfjs.mjs';

export const MAX_BYTES = 64 * 1024 * 1024;
const attr = (v, name, fallback) => v.attributes.find(a => a.name === name)?.value ?? fallback;
const scalar = value => Array.isArray(value) ? value[0] : value;
const flat = value => Array.isArray(value) ? value.flat(Infinity) : Array.from(value);

export function readNetCDF(buffer) {
  if (buffer.byteLength > MAX_BYTES) throw Error('Use the Python tool for files larger than 64 MiB.');
  const signature = new Uint8Array(buffer, 0, Math.min(4, buffer.byteLength));
  if (signature[0] !== 67 || signature[1] !== 68 || signature[2] !== 70 || ![1,2].includes(signature[3]))
    throw Error('This browser tool supports NetCDF3 classic and 64-bit offset files. Use the Python tool for NetCDF4/HDF5.');
  return new NetCDFReader(buffer);
}

export function dimensions(reader, variable) {
  return variable.dimensions.map(id => ({name: reader.dimensions[id].name,
    size: reader.dimensions[id].size || reader.recordDimension.length}));
}

function axis(values, name, limit) {
  if (values.length < 2 || values.some(v => !Number.isFinite(v) || Math.abs(v) > limit))
    throw Error(`${name} needs at least two finite coordinate centers in geographic degrees.`);
  const step = values[1] - values[0];
  if (!step || values.slice(1).some((v,i) => (v-values[i])*step <= 0 || Math.abs(v-values[i]-step) > Math.abs(step)*1e-5+1e-8))
    throw Error(`${name} must be monotonic and regularly spaced. Regrid irregular or dateline-crossing data first.`);
  return Math.abs(step);
}

function decoded(reader, variable) {
  if (String(attr(variable,'_Unsigned','false')).toLowerCase() === 'true')
    throw Error('Unsigned packed variables require the Python tool.');
  const fill = [attr(variable,'_FillValue',NaN), attr(variable,'missing_value',NaN)].flat();
  const defaults = {byte:-127,short:-32767,int:-2147483647,float:9.969209968386869e36,double:9.969209968386869e36};
  fill.push(defaults[variable.type]);
  const scale = Number(scalar(attr(variable,'scale_factor',1)));
  const offset = Number(scalar(attr(variable,'add_offset',0)));
  if (!Number.isFinite(scale) || !Number.isFinite(offset)) throw Error('Invalid scale or offset metadata.');
  return flat(reader.getDataVariable(variable)).map(v => !Number.isFinite(v) || fill.includes(v) ? NaN : v*scale+offset);
}

export function convertGrid(reader, variableName, latitudeName, longitudeName, selectors={}) {
  const get = name => {const v=reader.variables.find(v=>v.name===name); if(!v)throw Error(`Variable ${name} not found.`); return v;};
  const v=get(variableName), lat=get(latitudeName), lon=get(longitudeName);
  if (v.type === 'char') throw Error('Choose a numeric data variable.');
  for(const c of [lat,lon]) {
    const units=String(attr(c,'units','')).toLowerCase();
    if(units && !['degrees','degree','degrees_north','degrees_east','degree_north','degree_east'].includes(units))
      throw Error('Coordinate units must be geographic degrees.');
  }
  const mapping=attr(v,'grid_mapping',null);
  if(mapping && attr(get(mapping),'grid_mapping_name','latitude_longitude')!=='latitude_longitude')
    throw Error('Projected grids need the Python/reprojection workflow.');
  const ld=dimensions(reader,lat), od=dimensions(reader,lon);
  const la=decoded(reader,lat), lo=decoded(reader,lon);
  let ys,xs,ydim,xdim;
  if(ld.length===1 && od.length===1){ys=la;xs=lo;ydim=ld[0].name;xdim=od[0].name;}
  else if(ld.length===2 && od.length===2 && ld.every((d,i)=>d.name===od[i].name && d.size===od[i].size)) {
    const [h,w]=ld.map(d=>d.size); ydim=ld[0].name;xdim=ld[1].name;
    ys=Array.from({length:h},(_,i)=>la[i*w]);xs=lo.slice(0,w);
    if(la.some((v,i)=>!Number.isFinite(v)||Math.abs(v-ys[Math.floor(i/w)])>1e-7) || lo.some((v,i)=>!Number.isFinite(v)||Math.abs(v-xs[i%w])>1e-7))
      throw Error('Curvilinear coordinates require regridding before conversion.');
  } else throw Error('Choose 1D axes or matching rectilinear 2D coordinates.');
  const dx=axis(xs,'Longitude',180),dy=axis(ys,'Latitude',90);
  if(ydim===xdim)throw Error('Latitude and longitude must use different spatial dimensions.');
  const dims=dimensions(reader,v);
  if(!dims.some(d=>d.name===ydim && d.size===ys.length)||!dims.some(d=>d.name===xdim && d.size===xs.length))throw Error('Coordinates do not match this variable.');
  for(const d of dims.filter(d=>![ydim,xdim].includes(d.name)))
    if(!Number.isInteger(selectors[d.name])||selectors[d.name]<0||selectors[d.name]>=d.size)throw Error(`Select an index for ${d.name} (0–${d.size-1}).`);
  const data=decoded(reader,v), width=xs.length,height=ys.length;
  if(data.length!==dims.reduce((n,d)=>n*d.size,1))throw Error('Unexpected data size; use the Python tool for this file.');
  const values=new Float64Array(width*height);
  for(let row=0;row<height;row++)for(let col=0;col<width;col++){
    const indices={...selectors,[ydim]:ys[0]<ys.at(-1)?height-1-row:row,[xdim]:xs[0]>xs.at(-1)?width-1-col:col};
    let index=0;for(const d of dims)index=index*d.size+indices[d.name];
    values[row*width+col]=data[index];
  }
  return {values,width,height,dx,dy,west:Math.min(xs[0],xs.at(-1))-dx/2,north:Math.max(ys[0],ys.at(-1))+dy/2,
    units:String(attr(v,'units','')),variable:variableName};
}

// Minimal uncompressed, single-band Float64 GeoTIFF, PixelIsArea, WGS84.
// Each TIFF tag is typed explicitly; external readers verify the output in tests.
export function writeGeoTIFF(grid) {
  const {width,height,values,dx,dy,west,north}=grid;
  const entries=[
    [256,4,[width]],[257,4,[height]],[258,3,[64]],[259,3,[1]],[262,3,[1]],
    [273,4,[0]],[277,3,[1]],[278,4,[height]],[279,4,[values.length*8]],
    [284,3,[1]],[339,3,[3]],[33550,12,[dx,dy,0]],[33922,12,[0,0,0,west,north,0]],
    [34735,3,[1,1,0,3,1024,0,1,2,1025,0,1,1,2048,0,1,4326]],
    [42113,2,[110,97,110,0]]
  ].sort((a,b)=>a[0]-b[0]);
  const sizes={2:1,3:2,4:4,12:8};
  let cursor=8+2+12*entries.length+4;
  const offsets=entries.map(([,type,data])=>{if(data.length*sizes[type]<=4)return null;cursor=Math.ceil(cursor/8)*8;const start=cursor;cursor+=data.length*sizes[type];return start;});
  cursor=Math.ceil(cursor/8)*8; entries.find(e=>e[0]===273)[2][0]=cursor;
  const buffer=new ArrayBuffer(cursor+values.length*8),view=new DataView(buffer);
  view.setUint16(0,0x4949,true);view.setUint16(2,42,true);view.setUint32(4,8,true);view.setUint16(8,entries.length,true);
  for(let i=0;i<entries.length;i++){
    const [tag,type,data]=entries[i],entry=10+12*i;
    view.setUint16(entry,tag,true);view.setUint16(entry+2,type,true);view.setUint32(entry+4,data.length,true);
    let at=offsets[i]??entry+8;if(offsets[i]!==null)view.setUint32(entry+8,at,true);
    for(const n of data){if(type===12)view.setFloat64(at,n,true);else if(type===4)view.setUint32(at,n,true);else if(type===3)view.setUint16(at,n,true);else view.setUint8(at,n);at+=sizes[type];}
  }
  values.forEach((v,i)=>view.setFloat64(cursor+8*i,v,true));
  return buffer;
}
