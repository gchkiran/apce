from app import app  # noqa: F401

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5014, debug=True)
