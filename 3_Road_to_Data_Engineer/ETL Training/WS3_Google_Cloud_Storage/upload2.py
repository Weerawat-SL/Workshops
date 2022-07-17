import sys
from google.cloud import storage


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )

if __name__ == "__main__":
    print(">> sys.argv",sys.argv)
    bucket = sys.argv[1]
    source_file = sys.argv[2]
    dest_file = sys.argv[3]
    upload_blob(bucket, source_file, dest_file)

#pythom3 (pyfile) (bucket) (source_file) (dest_file)