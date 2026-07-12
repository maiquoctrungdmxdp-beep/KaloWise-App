import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Cấu hình quyền truy cập
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# Mở file Sheets của bạn (thay tên file vào đây)
sheet = client.open("KaloWise").sheet1

# Lấy toàn bộ dữ liệu
data = sheet.get_all_records()
print(data)
