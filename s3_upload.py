#!/usr/bin/env python3

import os
import boto3
import logging
from pathlib import Path
from typing import List, Optional
from botocore.exceptions import ClientError, NoCredentialsError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class S3Uploader:
    """Handle uploading prison data to S3 bucket."""
    
    def __init__(self, bucket_name: str = "stilesdata.com", profile_name: Optional[str] = None):
        """
        Initialize S3 uploader.
        
        Args:
            bucket_name: S3 bucket name
            profile_name: AWS profile name (defaults to AWS_PROFILE_NAME env var)
        """
        self.bucket_name = bucket_name
        self.profile_name = profile_name or os.getenv('AWS_PROFILE_NAME')
        self.s3_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize S3 client with profile."""
        try:
            if self.profile_name:
                logger.info(f"Using AWS profile: {self.profile_name}")
                session = boto3.Session(profile_name=self.profile_name)
                self.s3_client = session.client('s3')
            else:
                logger.info("Using default AWS credentials")
                self.s3_client = boto3.client('s3')
            
            # Test connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Successfully connected to S3 bucket: {self.bucket_name}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure your credentials.")
            raise
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"Bucket {self.bucket_name} not found")
            elif error_code == '403':
                logger.error(f"Access denied to bucket {self.bucket_name}")
            else:
                logger.error(f"Error connecting to S3: {e}")
            raise
    
    def upload_file(self, local_path: str, s3_key: str, content_type: Optional[str] = None) -> bool:
        """
        Upload a single file to S3.
        
        Args:
            local_path: Path to local file
            s3_key: S3 object key (path in bucket)
            content_type: MIME type for the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            local_file = Path(local_path)
            if not local_file.exists():
                logger.error(f"Local file not found: {local_path}")
                return False
            
            # Determine content type if not provided
            if not content_type:
                content_type = self._get_content_type(local_file.suffix)
            
            # Upload file
            extra_args = {'ContentType': content_type} if content_type else {}
            
            logger.info(f"Uploading {local_path} to s3://{self.bucket_name}/{s3_key}")
            self.s3_client.upload_file(
                str(local_file), 
                self.bucket_name, 
                s3_key,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Successfully uploaded {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to upload {local_path}: {e}")
            return False
    
    def upload_directory(self, local_dir: str, s3_prefix: str = "") -> List[str]:
        """
        Upload entire directory to S3.
        
        Args:
            local_dir: Path to local directory
            s3_prefix: S3 prefix (folder path in bucket)
            
        Returns:
            List of successfully uploaded S3 keys
        """
        uploaded_files = []
        local_path = Path(local_dir)
        
        if not local_path.exists() or not local_path.is_dir():
            logger.error(f"Directory not found: {local_dir}")
            return uploaded_files
        
        # Walk through all files in directory
        for file_path in local_path.rglob('*'):
            if file_path.is_file():
                # Calculate relative path from base directory
                relative_path = file_path.relative_to(local_path)
                
                # Construct S3 key
                if s3_prefix:
                    s3_key = f"{s3_prefix.rstrip('/')}/{relative_path}"
                else:
                    s3_key = str(relative_path)
                
                # Upload file
                if self.upload_file(str(file_path), s3_key):
                    uploaded_files.append(s3_key)
        
        return uploaded_files
    
    def upload_prison_data(self, data_dir: str = "data") -> dict:
        """
        Upload all prison data to S3 with organized structure.
        
        Args:
            data_dir: Local data directory path
            
        Returns:
            Dictionary with upload results by jurisdiction
        """
        results = {}
        data_path = Path(data_dir)
        
        if not data_path.exists():
            logger.error(f"Data directory not found: {data_dir}")
            return results
        
        # Upload each jurisdiction's data
        for jurisdiction_dir in data_path.iterdir():
            if jurisdiction_dir.is_dir():
                jurisdiction_name = jurisdiction_dir.name
                logger.info(f"Uploading {jurisdiction_name} data...")
                
                # Upload to prisons/{jurisdiction}/ in S3
                s3_prefix = f"prisons/{jurisdiction_name}"
                uploaded_files = self.upload_directory(str(jurisdiction_dir), s3_prefix)
                
                results[jurisdiction_name] = {
                    'files_uploaded': len(uploaded_files),
                    'files': uploaded_files
                }
                
                logger.info(f"Uploaded {len(uploaded_files)} files for {jurisdiction_name}")
        
        return results
    
    def _get_content_type(self, file_extension: str) -> str:
        """Get MIME type based on file extension."""
        content_types = {
            '.json': 'application/json',
            '.csv': 'text/csv',
            '.geojson': 'application/geo+json',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.py': 'text/x-python'
        }
        return content_types.get(file_extension.lower(), 'application/octet-stream')
    
    def list_bucket_contents(self, prefix: str = "prisons/") -> List[str]:
        """
        List contents of S3 bucket with given prefix.
        
        Args:
            prefix: S3 prefix to filter objects
            
        Returns:
            List of S3 object keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            else:
                return []
                
        except ClientError as e:
            logger.error(f"Failed to list bucket contents: {e}")
            return []
    
    def generate_public_urls(self, jurisdiction: str) -> dict:
        """
        Generate public URLs for a jurisdiction's data files.
        
        Args:
            jurisdiction: Name of jurisdiction
            
        Returns:
            Dictionary with file types and their URLs
        """
        base_url = f"https://{self.bucket_name}"
        urls = {}
        
        file_types = ['json', 'csv', 'geojson']
        for file_type in file_types:
            key = f"prisons/{jurisdiction}/{jurisdiction}_prisons.{file_type}"
            urls[file_type] = f"{base_url}/{key}"
        
        return urls


def main():
    """Main function for testing S3 upload functionality."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload prison data to S3')
    parser.add_argument('--data-dir', default='data', help='Local data directory')
    parser.add_argument('--bucket', default='stilesdata.com', help='S3 bucket name')
    parser.add_argument('--profile', help='AWS profile name (overrides AWS_PROFILE_NAME)')
    parser.add_argument('--list', action='store_true', help='List current S3 contents')
    parser.add_argument('--urls', help='Generate public URLs for jurisdiction')
    
    args = parser.parse_args()
    
    try:
        # Initialize uploader
        uploader = S3Uploader(bucket_name=args.bucket, profile_name=args.profile)
        
        if args.list:
            # List bucket contents
            contents = uploader.list_bucket_contents()
            print(f"S3 bucket contents ({len(contents)} objects):")
            for key in contents:
                print(f"  {key}")
        
        elif args.urls:
            # Generate URLs for jurisdiction
            urls = uploader.generate_public_urls(args.urls)
            print(f"Public URLs for {args.urls}:")
            for file_type, url in urls.items():
                print(f"  {file_type.upper()}: {url}")
        
        else:
            # Upload data
            print("Starting S3 upload...")
            results = uploader.upload_prison_data(args.data_dir)
            
            print("\nUpload Summary:")
            print("=" * 50)
            total_files = 0
            for jurisdiction, result in results.items():
                files_count = result['files_uploaded']
                total_files += files_count
                print(f"{jurisdiction}: {files_count} files")
            
            print(f"\nTotal files uploaded: {total_files}")
            print(f"Data available at: https://{args.bucket}/prisons/")
    
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
