import os
import sys
from typing import Dict, Any

# Thêm thư mục gốc vào sys.path để có thể import các module crawl
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir)) # /Users/toan/Working/localAPI
sys.path.append(root_dir)

# Import các module crawl từ thư mục crawl
from crawl.crawlTimeTable import scrape_timetables
from crawl.crawlResult import scrape_student_data
from crawl.crawlDataFlow import main as upload_data

class CrawlService:
    def __init__(self):
        # Thư mục lưu kết quả crawl
        self.output_dir = os.path.join(root_dir, "crawl_test")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Thư mục ChromaDB
        self.chroma_dir = os.path.join(root_dir, "chromadb_data")
        os.makedirs(self.chroma_dir, exist_ok=True)

    def process_crawl(self, username: str, password: str) -> Dict[str, Any]:
        try:
            # Đặt biến môi trường cho thư mục output
            os.environ["SOURCE_DIRECTORY"] = self.output_dir
            os.environ["CHROMA_PERSIST_DIRECTORY"] = self.chroma_dir
            os.environ["COLLECTION_NAME"] = "test_ute"
            
            # Crawl thời khóa biểu
            timetables_md, timetable_file = scrape_timetables(
                username=username,
                password=password,
                output_dir=self.output_dir
            )

            # Crawl kết quả học tập
            student_data, result_file = scrape_student_data(
                username=username,
                password=password,
                output_dir=self.output_dir
            )

            # Upload dữ liệu lên ChromaDB
            upload_data()

            return {
                "status": "success",
                "message": "Crawl và upload dữ liệu thành công",
                "data": {
                    "timetable_file": timetable_file,
                    "result_file": result_file
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Lỗi khi crawl dữ liệu: {str(e)}",
                "data": None
            }

# Khởi tạo singleton instance
crawl_service = CrawlService() 