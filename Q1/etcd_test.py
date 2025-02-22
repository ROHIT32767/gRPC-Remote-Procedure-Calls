import etcd3

def test_etcd_connection():
    try:
        client = etcd3.client()
        print("Connected to etcd successfully")
    except Exception as e:
        print(f"Failed to connect to etcd: {e}")

if __name__ == '__main__':
    test_etcd_connection()