# Tổng quan

Repo này là một hệ thống chatbot toàn diện được xây dựng để phục vụ cho Trường Đại học Sư phạm Kỹ thuật Hưng Yên (UTEHY), sử dụng Retrieval-Augmented Generation (RAG) để cung cấp câu trả lời chính xác từ cơ sở tri thức của trường.
Dự án sử dụng hybrid search bao gồm vector search và BM25 để tìm kiếm k đoạn văn bản liên quan đến câu hỏi => re-rank để lấy ra k` đoạn liên quan nhất truyền vào LLM để sinh câu hỏi
Ngoài ra, repo này cũng tiến hành fine-tuning embedding models và LLM để nâng cao hiệu quả cho tác vụ hỏi đáp dựa trên ngữ cảnh liên quan đến chủ đề trường đại học.


Link slide: https://www.canva.com/design/DAGpKgWqm3o/3LP1ytj6C_n8L-B_lmJNCw/edit?utm_content=DAGpKgWqm3o&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton
