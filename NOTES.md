
✅ **S3 Upload Implemented**: Data sets are now automatically uploaded to S3 bucket `stilesdata.com > prisons` using AWS profile from `AWS_PROFILE_NAME`. 

**Usage**:
- `python fetch.py --states michigan --upload-s3` - Scrape and upload
- `python s3_upload.py` - Upload all existing data
- `python s3_upload.py --list` - List bucket contents
- `python s3_upload.py --urls michigan` - Get public URLs

**Public Access**: https://stilesdata.com/prisons/{jurisdiction}/{jurisdiction}_prisons.{json|csv|geojson} 