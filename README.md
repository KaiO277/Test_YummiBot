# Setup

## Tạo môi trường ảo

```
python -m venv venv
```

## Khởi chạy môi trường ảo

```
.\venv\Scripts\activate
```

## Cài đặt thư viện cho project

### Di chuyển đến folder chứa file requirements.txt

```
cd food-recommend-api
```

### Nhập lệnh để cài đặt thư viện

```
pip install -r requirements.txt
```

# Chạy dự án

```
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

# Test API

Truy cập trình duyệt:

```
http://127.0.0.1:8001/docs
```
