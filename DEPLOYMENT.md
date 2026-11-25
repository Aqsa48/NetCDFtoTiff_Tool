# Deploy with GitHub Pages

The browser converter is a static website. GitHub Pages serves it, and GitHub Actions runs the checks and publishes the files from this repository.

## Repository setup

Under **Settings → Pages → Build and deployment**, select **GitHub Actions** as the source. The repository's `github-pages` environment must allow deployments from `main`. No custom domain or additional secrets are required.

## Publish an update

Push changes to `web/`, the Python converter, its tests, or the deployment workflow on `main`. The **Deploy GitHub Pages** workflow will:

1. Test the Python converter.
2. Convert the browser's synthetic NetCDF fixture and check the resulting TIFF independently with Rasterio.
3. Package only the public HTML, CSS, JavaScript, sample data, and license notices.
4. Deploy the artifact to GitHub Pages after all checks pass.

Documentation-only changes do not redeploy the website. To publish manually, open **Actions → Deploy GitHub Pages → Run workflow**, select `main`, and run it. GitHub shows the published URL in the deployment job and environment.

The live project address is https://aqsabrohi.me/NetCDFtoTiff_Tool/. The account's existing `Aqsa48.github.io` repository configures `aqsabrohi.me` as its custom domain, so https://aqsa48.github.io/NetCDFtoTiff_Tool/ redirects to that domain. This website is served by GitHub Pages and deployed by GitHub Actions. Use the HTTPS custom-domain link directly. All browser asset URLs are relative so the app works under the repository's path.

## Check the live demo

Open the published site, select **Try a synthetic example**, then **Create GeoTIFF**. Time index `0` should show a 3 × 2 raster, five valid cells, one missing cell, and west/north edges of `6.5` / `46.5`. Download the TIFF and open it in a GIS viewer if needed. Time index `1` should have six valid cells.

## If publication fails

Check the failed job's log in Actions. A missing Pages configuration usually means the repository source is not set to GitHub Actions. A pending environment approval means a configured deployment protection rule needs the repository owner's attention. Fix the reported condition and rerun the failed job.

No Python process runs on GitHub Pages. Visitors' files are processed in their own browser; NetCDF4/HDF5 and larger files use the separately installable Python tool.
