# MASTER DEVELOPMENT BLUEPRINT

> Tài liệu chi tiết: Vấn đề, Giải pháp, Requirements, Modules, Các Phase, Công nghệ và Codebase.

## 0. CODING AGENT CONTRACT

- Luôn ưu tiên G1 requirements và ràng buộc người dùng trước mọi gợi ý kỹ thuật.
- Không dùng benchmark/con số trong CoResearch làm target hoặc ngưỡng pass/fail nếu user chưa xác nhận.
- Mỗi file/hàm cần bám `addresses`/requirement IDs tương ứng; nếu thiếu mapping, ghi rõ TODO/assumption thay vì tự đặt mục tiêu mới.
- Giữ module boundary: module chỉ phụ thuộc module khác khi có input/output contract trực tiếp hoặc dependency đã nêu trong design package.
- Output code nên có test/validation tương ứng với acceptance criteria, không chỉ chạy được về mặt cú pháp.

## 1. VẤN ĐỀ (PROBLEM PROFILE)

**Business Goal:** Tạo bản báo cáo insight và phân tích dữ liệu từ bộ dataset Olist, tập trung vào ba trục chính: giữ chân khách hàng, hiệu quả giao vận và tăng trưởng doanh thu.
**Technical Objective:** Phân tích dữ liệu dạng bảng có thành phần thời gian (time series), văn bản (review) và địa lý (geospatial) từ 9 bảng quan hệ với khoảng 100,000 đơn hàng trong khoảng thời gian 32 tháng, tạo ra báo cáo insight đa chiều.

### Success Criteria
- {'target': '6-10 insight chính được trình bày với số liệu cụ thể, kèm khuyến nghị hành động có thể triển khai', 'description': 'Bản báo cáo insight hoàn chỉnh bao gồm phân tích theo ba trục: giữ chân khách hàng (tỷ lệ mua lặp lại, thời gian mua lại, giá trị vòng đời), giao hàng chậm trễ (tỷ lệ trễ, phân bổ theo khu vực/người bán/danh mục, tác động đến đánh giá) và xu hướng doanh thu (theo thời gian, danh mục, khu vực, phương thức thanh toán)', 'criterion_id': 'SC-001', 'verification_method': 'Kiểm tra tính đầy đủ của các phân tích trên dữ liệu Olist thực tế, xác nhận có bằng chứng định lượng rõ ràng cho mỗi insight', 'requires_user_confirmation': False}
- {'target': 'Không có lỗi đếm trùng hoặc tính nhầm hạt dữ liệu trong các chỉ số chính', 'description': 'Các chỉ số và insight được tính toán chính xác, tránh đếm trùng khách hàng (dùng customer_unique_id), đếm trùng doanh thu (tổng hợp payment theo order_id trước) và tính nhầm giao trễ (chỉ tính trên đơn đã giao có đủ ngày dự kiến và thực tế)', 'criterion_id': 'SC-002', 'verification_method': 'Review logic tính toán các chỉ số theo data contract đã xác lập: customer_unique_id cho khách hàng thật, order_id là hạt đơn hàng, tách rõ doanh thu hàng hóa/phí vận chuyển/thanh toán', 'requires_user_confirmation': False}
- {'target': 'Ma trận ưu tiên can thiệp rõ ràng với ít nhất 3-5 khuyến nghị có tác động cao được xác định cụ thể', 'description': 'Khuyến nghị hành động được phân loại theo tác động kinh doanh, độ khó triển khai và rủi ro, giúp nhóm quản trị ưu tiên can thiệp có giá trị', 'criterion_id': 'SC-003', 'verification_method': 'Xem xét ma trận khuyến nghị theo quy mô × mức độ × tác động trải nghiệm, đảm bảo các khuyến nghị nằm ở giao điểm giữa giá trị kinh tế, rủi ro trải nghiệm và khả năng triển khai nhanh [cite: cr_0143]', 'requires_user_confirmation': False}

### Data Profile
- **Data type:** tabular
- **Volume:** ~100,000 đơn hàng (orders: 99,441 rows; order_items: 112,650 rows do multi-item orders; payments: 103,886 rows do multi-payment orders; customers: 99,441 rows với ~96,096 unique customers)

### Constraints
**Hạ tầng:**
- Laptop cá nhân không có GPU, RAM 8GB — giới hạn khả năng xử lý in-memory cho dataset lớn và model phức tạp
**Tuân thủ:**
- Dữ liệu đã được ẩn danh hóa (tên công ty trong review text thay bằng Game of Thrones characters), license CC BY-NC-SA 4.0 cho phép sử dụng phi thương mại với chia sẻ tương tự
**Vấn đề/rủi ro:**
- [Note: Data Quality] Có thể có dữ liệu định vị (geolocation) trùng lặp hoặc thiếu ổn định theo zip code. Nên ưu tiên phân tích theo bang/thành phố thay vì zip code chi tiết khi tính khoảng cách. [cite: cr_0070]
- [Note: Time Coverage] Dữ liệu chỉ bao phủ 32 tháng (01/2016-08/2018), có thể bị ảnh hưởng bởi mùa vụ, thay đổi chính sách sàn và điều kiện hậu cần tại thời điểm cụ thể ở Brazil. Các khuyến nghị nên được thử nghiệm có nhóm đối chứng. [cite: cr_0156]
- [Note: Missing Cost Data] Dataset không có thông tin chi phí, lợi nhuận, chi phí thu hút khách hàng, chi phí vận chuyển thực tế và hành vi khách hàng ngoài giao dịch (browsing, cart abandonment). Giá trị vòng đời chỉ có thể tính theo doanh thu quan sát được. [cite: cr_0141]
- [Risk: Trung bình] Rủi ro tính nhầm giao trễ nếu so sánh timestamp thay vì ngày — phải chuẩn hóa về DATE trước khi so sánh SLA để tránh phóng đại tỷ lệ trễ. [cite: cr_0087]
- [Risk: Trung bình] Rủi ro nhân bản đơn khi nối order_items/payments trực tiếp với orders mà không tổng hợp — sẽ sai tỷ lệ trễ và doanh thu liên quan. Biện pháp kiểm soát: tạo bảng theo đúng hạt (đơn, đơn-người bán, đơn-danh mục). [cite: cr_0087]
- [Risk: Thấp] Xếp hạng người bán dựa trên mẫu nhỏ (ít đơn nhưng tỷ lệ trễ cực đoan) có thể tạo kết luận sai lệch. Nên chuẩn hóa theo danh mục, bang và quy mô đơn khi xếp hạng. [cite: cr_0087, cr_0152]

## 1.1 ANALYSIS TASK GRAPH

### AT-001 — Phân tích đa chiều bộ dữ liệu Olist E-Commerce (Primary)
- **Objective:** Tạo ra bản báo cáo insight hoàn chỉnh về giữ chân khách hàng, hiệu quả giao vận và xu hướng doanh thu từ 100,000 đơn hàng Olist, kèm ma trận ưu tiên khuyến nghị hành động
- **Outputs:** Báo cáo insight hoàn chỉnh với 6-10 insight chính có bằng chứng định lượng, Ma trận ưu tiên khuyến nghị (tác động × độ khó × rủi ro), Tập chỉ số và bảng tóm tắt đã được validate
- **Depends on:** None
- **Validation:** Kiểm tra từng subtask đã tạo output đúng định dạng và bao phủ success criteria tương ứng; Xác nhận không có dependency cycle giữa các subtask; Review logic tính toán chỉ số trong AT-002 theo data contract; Đối chiếu danh sách insight trong AT-003 với yêu cầu 3 trục phân tích; Kiểm tra ma trận khuyến nghị trong AT-004 có phân loại rõ ràng theo impact × feasibility × risk

### AT-002 — Xây dựng nền tảng dữ liệu đã validate và tính toán chỉ số nền
- **Objective:** Tạo các bảng dữ liệu đã được làm sạch, nối đúng hạt (grain) và tính toán chính xác các chỉ số nền cho 3 trục phân tích, tránh đếm trùng và tính nhầm logic
- **Outputs:** Bảng orders đã làm sạch với cột is_late, delivery_days, estimated_days, Bảng customer_summary với customer_unique_id, order_count, total_revenue, first_order_date, last_order_date, is_repeat, Bảng order_revenue tổng hợp payment_value theo order_id, tách product_value và freight_value, Bảng validation report xác nhận không có đếm trùng
- **Depends on:** None
- **Validation:** Đếm số lượng customer_unique_id duy nhất và so sánh với số đơn hàng để xác nhận tỷ lệ mua lặp lại hợp lý; Tổng doanh thu từ bảng order_revenue phải khớp với tổng payment_value từ bảng payments gốc; Tính tỷ lệ đơn giao trễ chỉ trên tập đơn có delivered status và có đủ cả hai timestamp giao hàng; Kiểm tra không có order_id bị trùng sau khi tổng hợp payment

### AT-003 — Phân tích ba trục kinh doanh và tạo insight định lượng
- **Objective:** Thực hiện phân tích chuyên sâu theo 3 trục (giữ chân khách hàng, giao hàng chậm trễ, xu hướng doanh thu), tạo ra 6-10 insight chính có bằng chứng số liệu cụ thể
- **Outputs:** Insight cluster 1 (retention): tỷ lệ mua lặp lại, khoảng thời gian mua lại trung bình, CLV theo cohort, Insight cluster 2 (delivery): tỷ lệ giao trễ tổng thể, phân bổ theo bang/khu vực/người bán/danh mục, tác động lên review score, Insight cluster 3 (revenue): xu hướng doanh thu theo tháng, top danh mục, tỷ trọng phương thức thanh toán, mùa vụ, Danh sách 6-10 insight chính với bằng chứng định lượng rõ ràng
- **Depends on:** AT-002
- **Validation:** Kiểm tra mỗi insight có kèm số liệu cụ thể (tỷ lệ %, số tuyệt đối, xu hướng thời gian); Xác nhận phân tích bao phủ đủ 3 trục theo problem statement; Đối chiếu insight với dữ liệu thực tế Olist (ví dụ: tỷ lệ mua lặp lại phải nhỏ vì marketplace thường có repeat rate thấp); Review các phân tích geospatial chỉ dùng bang/thành phố như khuyến nghị trong noted_issues

### AT-004 — Tổng hợp khuyến nghị hành động và tạo ma trận ưu tiên
- **Objective:** Chuyển các insight thành khuyến nghị hành động cụ thể, phân loại theo tác động kinh doanh × độ khó triển khai × rủi ro, tạo ma trận ưu tiên cho nhóm quản trị Olist
- **Outputs:** Danh sách 3-5 khuyến nghị ưu tiên cao với mô tả hành động cụ thể, Ma trận ưu tiên (impact × feasibility × risk) cho tất cả khuyến nghị, Phân loại khuyến nghị theo loại can thiệp (chăm sóc khách hàng / giao vận / danh mục / SLA người bán)
- **Depends on:** AT-003
- **Validation:** Kiểm tra mỗi khuyến nghị có gắn với ít nhất một insight từ AT-003; Xác nhận có ít nhất 3-5 khuyến nghị nằm ở góc phần tư cao-impact × high-feasibility; Review khuyến nghị không yêu cầu dữ liệu thiếu (chi phí, lợi nhuận, browsing behavior) hoặc nêu rõ giới hạn; Đối chiếu với decision context để đảm bảo khuyến nghị phù hợp với khả năng can thiệp của Olist

### AT-005 — Biên soạn báo cáo insight cuối cùng
- **Objective:** Tổng hợp tất cả phân tích, insight và khuyến nghị thành một báo cáo duy nhất, có cấu trúc rõ ràng và trình bày bằng chứng định lượng dễ hiểu cho nhóm quản trị
- **Outputs:** Báo cáo insight hoàn chỉnh với cấu trúc: tóm tắt điều hành, phương pháp và data quality, phân tích 3 trục, insight chính, ma trận khuyến nghị, Phụ lục kỹ thuật: logic tính toán chỉ số, validation report, giả định và giới hạn
- **Depends on:** AT-002, AT-003, AT-004
- **Validation:** Đối chiếu báo cáo với từng success criterion: SC-001 (6-10 insight × 3 trục), SC-002 (validation report kèm theo), SC-003 (ma trận ưu tiên 3-5 khuyến nghị); Kiểm tra báo cáo có trả lời đầy đủ problem statement và phục vụ decision context; Xác nhận không có missing_inputs nghiêm trọng chưa được xử lý hoặc ghi chú; Review báo cáo dễ đọc, có visualizations nếu cần và nêu rõ giới hạn (thiếu dữ liệu chi phí, chỉ 32 tháng)

---

## 2. GIẢI PHÁP (SOLUTION STRATEGY)

- **Family:** Multi-Dimensional Descriptive Analytics với Controlled Correlation Analysis
- **Rationale:** Bài toán yêu cầu phân tích mô tả (descriptive analytics) đa chiều trên dữ liệu quan hệ, tập trung vào ba trục: giữ chân khách hàng, giao vận và doanh thu. Không phải bài toán dự đoán (predictive) hay nhân quả (causal inference) chính thức, nhưng cần phân tích liên hệ có kiểm soát (controlled correlation) để nhận diện tín hiệu hành động. Phương pháp cohort analysis, SLA-based classification, revenue decomposition và segmentation phù hợp với loại dữ liệu (100,000 đơn hàng, 32 tháng, 9 bảng quan hệ) và mục tiêu đầu ra (insight + khuyến nghị có thể hành động)


---

## 3. YÊU CẦU (REQUIREMENTS)

> Danh sách này mô tả những điều kiện agent hiểu là cần có để giải quyết đúng bài toán. User nên đọc và đánh giá nội dung, không phải một schema traceability bắt buộc.

- **FR-01**: Đếm khách hàng thật qua customer_unique_id
  - Requirement: Mọi phân tích về khách hàng (tỷ lệ mua lặp lại, CLV, cohort) phải dùng `customer_unique_id` từ bảng `customers`, không dùng `customer_id` từ bảng `orders` vì mỗi đơn hàng có một `customer_id` riêng dù cùng một người mua
  - Vì sao cần: Required to keep the requirement tied to the user problem and downstream validation.
  - Cách kiểm tra/xác nhận: ["Bảng customer_summary phải group theo customer_unique_id", "Tỷ lệ mua lặp lại = (số customer_unique_id có order_count ≥ 2) / (tổng số customer_unique_id)", "Validation report xác nhận tổng số customer_unique_id duy nhất khớp với số lượng khách hàng thật trong dataset"]
- **FR-02**: Tổng hợp doanh thu theo hạt order_id
  - Requirement: Doanh thu phải được tổng hợp từ bảng `order_payments` theo `order_id` trước khi nối với bảng `orders`, tách rõ `product_value` và `freight_value`. Không lấy trực tiếp `price` hoặc `freight_value` từ `order_items` vì một đơn có thể có nhiều item và nhiều giao dịch thanh toán
  - Vì sao cần: Required to keep the requirement tied to the user problem and downstream validation.
  - Cách kiểm tra/xác nhận: ["Tạo bảng order_revenue với order_id là khóa chính, chứa tổng payment_value từ order_payments", "Tổng doanh thu từ order_revenue phải bằng tổng payment_value từ bảng order_payments gốc (cho tập đơn đã giao)", "Validation report xác nhận không có order_id bị đếm nhiều lần trong phân tích doanh thu"]
- **FR-03**: Tính giao hàng chậm trễ chỉ trên đơn đã giao đủ timestamp
  - Requirement: Tỷ lệ giao trễ chỉ được tính trên tập đơn có `order_status = 'delivered'` và có đủ cả hai cột `order_delivered_customer_date` (ngày giao thực tế) và `order_estimated_delivery_date` (ngày giao ước tính). Đơn chậm trễ là đơn có `order_delivered_customer_date > order_estimated_delivery_date`
  - Vì sao cần: Required to keep the requirement tied to the user problem and downstream validation.
  - Cách kiểm tra/xác nhận: ["Bảng orders đã làm sạch có cột `is_late` (boolean) được tính từ so sánh hai timestamp trên", "Tỷ lệ giao trễ = (số đơn is_late = true) / (số đơn delivered có đủ cả hai timestamp)", "Validation report ghi rõ số đơn bị loại do thiếu timestamp hoặc chưa giao"]
- **FR-04**: Phân tích theo ba trục đã xác định
  - Requirement: Báo cáo phải bao gồm phân tích đầy đủ theo ba trục: (1) Giữ chân khách hàng (tỷ lệ mua lặp lại, thời gian mua lại, CLV theo cohort), (2) Giao hàng chậm trễ (tỷ lệ trễ tổng thể, phân bổ theo bang/khu vực/người bán/danh mục, tác động lên review score), (3) Xu hướng doanh thu (theo tháng, top danh mục, phương thức thanh toán, mùa vụ)
  - Vì sao cần: Required to keep the requirement tied to the user problem and downstream validation.
  - Cách kiểm tra/xác nhận: ["Báo cáo có ba phần (hoặc cluster) tương ứng với ba trục, mỗi phần có ít nhất 2-3 insight chính", "Mỗi insight kèm bằng chứng định lượng cụ thể (tỷ lệ %, số tuyệt đối, xu hướng thời gian)", "Tổng cộng có 6-10 insight chính như yêu cầu trong SC-001"]
- **FR-05**: Phân tích địa lý ưu tiên theo bang và thành phố
  - Requirement: Phân tích geospatial (giao trễ theo khu vực, phân bổ khách hàng/người bán) phải ưu tiên dùng cột `customer_state` (bang) và `customer_city` (thành phố) từ bảng customers và sellers. Chỉ dùng `geolocation_zip_code_prefix` khi cần tính khoảng cách giữa seller và customer, không phân tích chi tiết theo zip code vì dữ liệu geolocation có thể trùng lặp hoặc thiếu
  - Vì sao cần: Required to keep the requirement tied to the user problem and downstream validation.
  - Cách kiểm tra/xác nhận: ["Phân tích giao trễ theo bang được trình bày bằng tỷ lệ trễ của từng bang, xếp hạng top bang có tỷ lệ trễ cao nhất", "Nếu tính khoảng cách seller-customer, ghi rõ phương pháp (haversine từ lat/lng trung bình theo zip code prefix) và giới hạn độ tin cậy", "Không có phân tích chi tiết theo từng zip code cụ thể trừ khi user xác nhận cần"]
- **FR-06**: Insight có bằng chứng định lượng rõ ràng
  - Requirement: Mỗi insight trong báo cáo phải kèm theo bằng chứng định lượng cụ thể: tỷ lệ phần trăm, số tuyệt đối, xu hướng thời gian (tăng/giảm bao nhiêu %), hoặc so sánh giữa các nhóm. Không dùng câu mơ hồ như 'có xu hướng tăng' mà phải ghi rõ 'tăng X% từ tháng A đến tháng B'
  - Vì sao cần: Required to keep the requirement tied to the user problem and downstream validation.
  - Cách kiểm tra/xác nhận: ["Mỗi insight trong danh sách 6-10 insight chính có ít nhất một con số cụ thể (tỷ lệ, số đếm, tốc độ tăng trưởng)", "Nếu nói về xu hướng, phải có ít nhất hai điểm thời gian để so sánh hoặc tốc độ tăng/giảm trung bình", "Validation kiểm tra không có insight chỉ dựa trên suy luận mà không có số liệu từ dataset Olist"]
- **FR-07**: Khuyến nghị phân loại theo tác động × độ khó × rủi ro
  - Requirement: Mỗi khuyến nghị hành động phải được phân loại theo ba chiều: (1) Tác động kinh doanh (cao/trung/thấp), (2) Độ khó triển khai (dễ/trung bình/khó), (3) Rủi ro trải nghiệm khách hàng hoặc người bán (thấp/trung/cao). Ma trận ưu tiên phải highlight 3-5 khuyến nghị nằm ở góc cao-impact × high-feasibility × low-risk
  - Vì sao cần: Required to keep the requirement tied to the user problem and downstream validation.
  - Cách kiểm tra/xác nhận: ["Ma trận ưu tiên được trình bày dưới dạng bảng hoặc biểu đồ phân tán với ba trục", "Có ít nhất 3-5 khuyến nghị được đánh dấu 'ưu tiên cao' theo tiêu chí cao-impact × high-feasibility × low-risk", "Mỗi khuyến nghị có mô tả hành động cụ thể, không chỉ nói 'cải thiện X' mà phải ghi 'làm gì để cải thiện X'"]
- **FR-08**: Khuyến nghị gắn với insight đã phân tích
  - Requirement: Mỗi khuyến nghị phải truy xuất được về ít nhất một insight từ AT-003. Không đưa ra khuyến nghị dựa trên suy luận chung hoặc best practice ngành mà không có bằng chứng từ dữ liệu Olist
  - Vì sao cần: Required to keep the requirement tied to the user problem and downstream validation.
  - Cách kiểm tra/xác nhận: ["Báo cáo ghi rõ insight nào dẫn đến khuyến nghị nào (có thể dùng reference ID hoặc mô tả ngắn)", "Validation kiểm tra không có khuyến nghị 'mồ côi' (không gắn insight nào)", "Nếu khuyến nghị dựa trên CoResearch hoặc suy luận bên ngoài, phải ghi rõ nguồn và giới hạn"]
- **FR-09**: Báo cáo có cấu trúc rõ ràng và phụ lục kỹ thuật
  - Requirement: Báo cáo cuối cùng phải có cấu trúc: (1) Tóm tắt điều hành (executive summary), (2) Phương pháp và data quality, (3) Phân tích ba trục, (4) Insight chính (6-10 insight), (5) Ma trận khuyến nghị, (6) Phụ lục kỹ thuật (logic tính toán chỉ số, validation report, giả định và giới hạn)
  - Vì sao cần: Required to keep the requirement tied to the user problem and downstream validation.
  - Cách kiểm tra/xác nhận: ["Báo cáo có đủ 6 phần như mô tả trên", "Phụ lục kỹ thuật bao gồm: công thức tính các chỉ số chính (repeat rate, CLV, tỷ lệ trễ), validation report từ AT-002, danh sách giả định (VD: dùng revenue thay vì profit) và giới hạn (VD: không có dữ liệu chi phí)", "Validation đối chiếu báo cáo với từng success criterion: SC-001 (6-10 insight × 3 trục), SC-002 (validation report), SC-003 (ma trận 3-5 khuyến nghị)"]
- **FR-10**: Xử lý missing_inputs một cách minh bạch
  - Requirement: Báo cáo phải ghi rõ các thông tin thiếu đã được xác định trong problem profile (ngưỡng định lượng, độ ưu tiên chiều phân tích, định dạng output mong muốn) và cách xử lý: (1) Sử dụng giả định hợp lý nào, (2) Đưa ra nhiều kịch bản nào, (3) Giới hạn nào cần lưu ý
  - Vì sao cần: Required to keep the requirement tied to the user problem and downstream validation.
  - Cách kiểm tra/xác nhận: ["Phần 'Giả định và Giới hạn' trong phụ lục kỹ thuật liệt kê rõ các missing_inputs từ problem profile và cách xử lý", "Nếu có insight hoặc khuyến nghị phụ thuộc vào giả định mạnh (VD: ngưỡng repeat rate tốt là bao nhiêu), phải ghi chú rõ", "Validation kiểm tra không có insight nào dựa trên dữ liệu không tồn tại trong dataset Olist"]
- **FR-11**: Giới hạn phân tích theo hạ tầng thực tế
  - Requirement: Phân tích phải chạy được trên laptop cá nhân RAM 8GB không có GPU. Không sử dụng model machine learning nặng (deep learning, large language model), tránh load toàn bộ dataset vào memory cùng lúc nếu vượt ngưỡng RAM, ưu tiên xử lý theo batch hoặc dùng aggregation trước
  - Vì sao cần: Required to keep the requirement tied to the user problem and downstream validation.
  - Cách kiểm tra/xác nhận: ["Logic phân tích trong AT-002 và AT-003 không yêu cầu load toàn bộ 100,000 đơn với tất cả cột vào memory cùng lúc", "Nếu cần tính toán nặng (VD: khoảng cách geospatial cho tất cả cặp seller-customer), phải có chiến lược sampling hoặc aggregation trước theo bang/thành phố", "Validation report ghi rõ memory footprint ước tính hoặc chiến lược xử lý nếu dataset lớn hơn RAM"]
- **FR-12**: Tuân thủ license CC BY-NC-SA 4.0
  - Requirement: Phân tích và báo cáo chỉ được sử dụng cho mục đích phi thương mại và phải ghi rõ nguồn dataset Olist khi chia sẻ. Nếu báo cáo được chia sẻ công khai, phải kèm license tương tự (share-alike)
  - Vì sao cần: Required to keep the requirement tied to the user problem and downstream validation.
  - Cách kiểm tra/xác nhận: ["Báo cáo có ghi rõ nguồn dataset: 'Brazilian E-Commerce Public Dataset by Olist, Kaggle, CC BY-NC-SA 4.0'", "Nếu user hỏi về sử dụng thương mại, agent phải nhắc nhở license không cho phép", "Validation kiểm tra không có phần nào trong báo cáo vi phạm điều khoản ẩn danh hóa (VD: không cố gắng reverse-engineer tên công ty từ Game of Thrones characters)"]

---

## 4. CÁC PHASE (HIGH-LEVEL PIPELINE)

### Phase 1: Problem Setup
- **Mục tiêu:** Thiết lập nền tảng dữ liệu sạch, cấu trúc phân tích và validation pipeline để đảm bảo tính chính xác của các chỉ số nền cho ba trục: giữ chân khách hàng, giao vận và doanh thu. Tạo bộ bảng trung gian đã được validate (orders_clean, customer_summary, order_revenue) làm đầu vào tin cậy cho các phase phân tích tiếp theo.
  - **Step 1.1**: Load và validate schema đầu vào (Python pandas)
    - Input: 9 file CSV từ dataset Olist
    - Output: Báo cáo schema validation (số dòng, tỷ lệ missing value, phân bổ order_status), 9 DataFrame đã load vào memory
    - Addresses: FR-01, FR-02, FR-03
  - **Step 1.2**: Làm sạch và tính chỉ số giao hàng (Python pandas + datetime module)
    - Input: DataFrame orders gốc từ step 1.1
    - Output: Bảng orders_clean (order_id, customer_id, order_status, order_purchase_timestamp, order_estimated_delivery_date, order_delivered_customer_date, is_late, delivery_days). Báo cáo validation: số đơn bị loại do thiếu timestamp, tỷ lệ giao trễ trên tập đơn hợp lệ
    - Addresses: FR-03
  - **Step 1.3**: Tổng hợp doanh thu và tạo bảng khách hàng (SQL aggregation (DuckDB/SQLite) hoặc pandas groupby)
    - Input: DataFrame order_payments, orders_clean, customers từ step 1.1 và 1.2
    - Output: Bảng order_revenue (order_id, total_payment_value), bảng customer_summary (customer_unique_id, order_count, total_revenue, first_order_date, last_order_date). Báo cáo validation: tổng payment_value khớp với gốc, tổng số customer_unique_id duy nhất
    - Addresses: FR-01, FR-02, FR-04
### Phase 2: Baseline Evaluation
- **Mục tiêu:** Tính toán các chỉ số nền tảng (baseline metrics) trên toàn bộ dataset để làm mốc so sánh cho phân tích phức tạp và xác nhận giá trị gia tăng của insight đa chiều. Bao gồm: tỷ lệ mua lặp lại tổng thể, tỷ lệ giao trễ tổng thể, doanh thu theo tháng và theo danh mục chính, cùng với validation report đảm bảo không đếm trùng khách hàng, doanh thu và logic tính trễ đúng [Self-Inferred dựa trên Evaluation Protocol bước 4 trong G2.5]
  - **Step 2.1**: Tính baseline giữ chân khách hàng (Python pandas)
    - Input: Bảng customer_summary đã group theo customer_unique_id với order_count, first_order_date, last_order_date
    - Output: Tỷ lệ mua lặp lại tổng thể (%), thời gian mua lại trung bình (ngày), số khách hàng mua một lần vs. nhiều lần
    - Addresses: FR-01, FR-04
  - **Step 2.2**: Tính baseline giao hàng chậm trễ (Python pandas)
    - Input: Bảng orders với order_status, is_late, late_days, order_delivered_customer_date, order_estimated_delivery_date
    - Output: Tỷ lệ giao trễ tổng thể (%), số ngày trễ trung bình, số đơn bị loại do thiếu timestamp hoặc chưa giao [cite: cr_0017]
    - Addresses: FR-03, FR-04
  - **Step 2.3**: Tính baseline xu hướng doanh thu (Python pandas groupby + SQL aggregation)
    - Input: Bảng order_revenue (order_id, payment_value, product_value, freight_value) nối với orders (order_purchase_timestamp) và order_items (product_category_name)
    - Output: Doanh thu theo tháng, tốc độ tăng trưởng trung bình (%), top 5 danh mục sản phẩm theo doanh thu, tỷ lệ phí vận chuyển trên tổng doanh thu
    - Addresses: FR-02, FR-04, FR-06
### Phase 3: Candidate Modeling
- **Mục tiêu:** Xây dựng các bảng phân tích đa chiều (cohort retention, late delivery segmentation, revenue decomposition, correlation matrix) từ dữ liệu đã làm sạch, tạo nền tảng cho việc rút ra insight hành động ở phase 4. Phase này tập trung vào việc tính toán các chỉ số phân tích nâng cao theo ba trục: giữ chân khách hàng, giao vận và doanh thu, đồng thời kiểm tra tương quan có kiểm soát giữa các trục để nhận diện tín hiệu hành động [cite: cr_0093]
  - **Step 3.1**: Cohort retention analysis (Python pandas groupby + datetime module)
    - Input: Bảng customer_summary (customer_unique_id, first_order_date, order_count, total_revenue), bảng orders đã làm sạch có order_purchase_timestamp chuẩn hóa
    - Output: Bảng cohort retention matrix (cohort_month, age_month, retention_rate), bảng CLV theo cohort, phân bổ khách hàng theo số đơn (1, 2, 3+), thời gian mua lại trung bình
    - Addresses: FR-01, FR-04
  - **Step 3.2**: Late delivery và risk segmentation (Python pandas cut/qcut + SQL aggregation)
    - Input: Bảng orders có is_late, late_days, customer_state, seller_id, product_category, review_score; bảng customer_summary có repeat_purchase flag
    - Output: Bảng late_rate theo bang/danh mục/seller (top 10-15), bảng segmentation theo mức độ trễ và review_score, bảng so sánh repeat_rate giữa nhóm first-order experience (on-time vs late vs canceled)
    - Addresses: FR-03, FR-04, FR-05, FR-07
  - **Step 3.3**: Revenue decomposition và correlation analysis (Python pandas groupby + SQL aggregation (DuckDB/SQLite) + scipy.stats + statsmodels)
    - Input: Bảng order_revenue (order_id, product_value, freight_value, payment_value, payment_type), bảng orders có order_purchase_timestamp, customer_state, product_category, late_days, review_score; bảng customer_summary có repeat_purchase
    - Output: Bảng revenue_trend theo tháng (total_revenue, order_count, AOV, MoM_growth, freight_ratio), bảng top danh mục/bang/payment_type; ma trận tương quan giữa late_days, review_score, order_revenue, repeat_purchase với biến kiểm soát; bảng partial correlation coefficients
    - Addresses: FR-02, FR-04, FR-06
### Phase 4: Evaluation Review
- **Mục tiêu:** Xác minh tính chính xác của các chỉ số nền tảng (khách hàng, doanh thu, giao trễ), kiểm tra tính nhất quán logic tính toán và đánh giá chất lượng insight/khuyến nghị so với yêu cầu ban đầu, đảm bảo không có lỗi đếm trùng, tính nhầm hạt dữ liệu hoặc insight không có bằng chứng
  - **Step 4.1**: Validation Chỉ Số Nền (Python pandas assert + SQL COUNT DISTINCT, SUM validation)
    - Input: customer_summary, order_revenue, orders (cleaned với cột is_late), bảng customers gốc, bảng order_payments gốc
    - Output: Validation report với ba phần: (1) Số customer_unique_id duy nhất (expected vs actual), (2) Tổng doanh thu (expected vs actual, delta tuyệt đối và %), (3) Tỷ lệ giao trễ (số đơn đã giao có đủ timestamp, số đơn trễ, tỷ lệ %, số đơn bị loại và lý do)
  - **Step 4.2**: So Sánh Insight Với Baseline (Python pandas groupby + statsmodels (chi-square test, t-test cho so sánh tỷ lệ và trung bình giữa nhóm))
    - Input: Cohort retention matrix, risk segmentation table (repeat_rate theo nhóm), revenue decomposition (doanh thu theo tháng/danh mục/bang/phương thức thanh toán), baseline metrics (tỷ lệ mua lặp lại tổng thể, tỷ lệ giao trễ tổng thể, doanh thu tổng theo tháng)
    - Output: Baseline comparison report với ba phần: (1) Cohort retention vs baseline (chênh lệch tỷ lệ mua lặp lại giữa cohort tốt nhất và xấu nhất, p-value từ chi-square test), (2) Risk segmentation vs baseline (chênh lệch repeat_rate giữa nhóm rủi ro cao và thấp, p-value từ t-test), (3) Revenue decomposition vs baseline (top 3 danh mục/bang đóng góp % doanh thu, xu hướng MoM growth rate). Đánh dấu insight không đạt ngưỡng khác biệt có ý nghĩa (p > 0.05 hoặc effect size < 5%)
  - **Step 4.3**: Kiểm Tra Khuyến Nghị Có Bằng Chứng (Python pandas DataFrame + manual traceability check (mapping recommendation_id → insight_id → evidence))
    - Input: Ma trận ưu tiên khuyến nghị (recommendation_id, description, impact_score, difficulty_score, risk_score, priority_tier), danh sách 6-10 insight chính (insight_id, description, evidence_type, quantitative_value)
    - Output: Traceability matrix (recommendation_id → insight_id → evidence_summary) và danh sách khuyến nghị đạt chuẩn (có đầy đủ bằng chứng + phân loại) vs danh sách khuyến nghị bị loại (thiếu bằng chứng hoặc dựa trên giả định). Báo cáo cuối chỉ giữ 3-5 khuyến nghị ưu tiên cao đã được xác minh

---

## 5. CÔNG NGHỆ (TECHNOLOGY STACK)

| Task | Final Solution | Type | Addresses | Rationale / Trade-off |
|---|---|---|---|---|
| Xây dựng khung dữ liệu quan hệ và tính chỉ số khách hàng | Python pandas cho data wrangling + SQL (DuckDB embedded hoặc SQLite) cho aggregation | Bên ngoài |  | Dataset có 9 bảng quan hệ với ~100,000 đơn hàng cần join, aggregate và transform phức tạp. Pandas (Python standard cho data analysis) kết hợp SQL engine (DuckDB hoặc SQLite) đáp ứng yêu cầu xử lý dữ liệu quan hệ, tính cohort retention, group theo customer_unique_id. Không có thông tin về công cụ nội bộ trong internal KB có thể thay thế. Laptop RAM 8GB đủ cho in-memory processing với pandas (dataset ~100MB ước tính). [Self-Inferred] |
| Chuẩn hóa timestamp và tính giao hàng chậm trễ theo SLA | Python pandas + datetime module (built-in) | Bên ngoài |  | Yêu cầu chuẩn hóa order_purchase_timestamp, order_estimated_delivery_date, order_delivered_customer_date về cấp ngày (DATE) để so sánh SLA, loại bỏ đơn thiếu timestamp hoặc chưa giao. Pandas DataFrame hỗ trợ datetime operations (pd.to_datetime, dt.date) và boolean indexing để lọc đơn có order_status='delivered'. Python datetime module (built-in) hỗ trợ date comparison. Không có thông tin về công cụ nội bộ thay thế. [Self-Inferred] |
| Tổng hợp doanh thu theo order_id và phân rã theo nhiều chiều | Python pandas groupby + SQL aggregation (DuckDB/SQLite) | Bên ngoài |  | Yêu cầu tổng hợp order_payments (103,886 rows) theo order_id trước khi nối với orders (99,441 rows), tách product_value, freight_value, payment_value. Sau đó phân rã doanh thu theo tháng, danh mục, bang, phương thức thanh toán. Pandas groupby + SQL aggregation (GROUP BY, SUM) đáp ứng yêu cầu FR-02 (tổng hợp đúng hạt) và FR-04 (phân rã doanh thu). Không có thông tin về công cụ nội bộ thay thế. [Self-Inferred] |
| Phân tích tương quan có kiểm soát giữa các trục | Python scipy.stats + statsmodels (partial correlation, OLS regression với control variables) | Bên ngoài |  | Yêu cầu kiểm tra tương quan giữa late_days, review_score, order_revenue, repeat_purchase với biến kiểm soát (tháng mua, danh mục, bang). Scipy.stats cung cấp correlation functions (pearsonr, spearmanr); statsmodels cung cấp partial correlation và OLS regression để kiểm soát confounders. Dataset 100,000 đơn đủ lớn cho controlled correlation analysis. Không có thông tin về công cụ nội bộ thay thế. [Self-Inferred] |
| Phân nhóm rủi ro đa trục và so sánh repeat rate | Python pandas cut/qcut + SQL CASE WHEN cho segmentation logic | Bên ngoài |  | Yêu cầu phân nhóm khách hàng theo tổ hợp: trạng thái giao hàng đơn đầu, số ngày trễ (nhẹ/vừa/nặng), review_score, giá trị đơn hàng. So sánh repeat_rate giữa các nhóm. Pandas cut/qcut hỗ trợ binning liên tục (late_days, order_revenue); SQL CASE WHEN hỗ trợ segmentation logic phức tạp. Không có thông tin về công cụ nội bộ thay thế. [Self-Inferred] |
| Trực quan hóa insight (cohort heatmap, xu hướng doanh thu, phân bổ giao trễ) | Python matplotlib + seaborn (static plots) hoặc plotly (interactive plots) | Bên ngoài |  | Yêu cầu trực quan hóa cohort retention heatmap, xu hướng doanh thu theo tháng, phân bổ giao trễ theo bang/danh mục để hỗ trợ insight có bằng chứng định lượng (FR-06). Matplotlib/seaborn là thư viện chuẩn cho static visualization; Plotly cung cấp interactive plots phù hợp với báo cáo analysis_package. Không có thông tin về công cụ nội bộ thay thế. [Self-Inferred] |
| Tạo ma trận ưu tiên khuyến nghị (tác động × độ khó × rủi ro) | Python pandas DataFrame + manual scoring logic | Bên ngoài |  | Yêu cầu phân loại khuyến nghị theo ba chiều (tác động kinh doanh, độ khó triển khai, rủi ro trải nghiệm) và highlight 3-5 khuyến nghị ưu tiên cao (FR-07). Không phải bài toán optimization tự động mà là decision support manual. Pandas DataFrame đủ để lưu trữ và filter khuyến nghị theo scoring logic do user/analyst định nghĩa. Không có thông tin về công cụ nội bộ thay thế. [Self-Inferred] |
| Validation report (kiểm tra đếm trùng, khớp tổng doanh thu, tỷ lệ đơn bị loại) | Python pandas assert + SQL integrity checks (COUNT DISTINCT, SUM validation) | Bên ngoài |  | Yêu cầu validation report xác nhận không có đếm trùng khách hàng (FR-01), doanh thu tổng hợp khớp với bảng payments gốc (FR-02), tỷ lệ đơn bị loại do thiếu timestamp (FR-03). Pandas assert (DataFrame.equals, np.isclose) + SQL integrity checks (COUNT DISTINCT, SUM) đáp ứng yêu cầu validation logic. Không có thông tin về công cụ nội bộ thay thế. [Self-Inferred] |

---

## 6. MODULE & HIGH-LEVEL DESIGN (MODULAR DESIGN PACKAGE)

### DM-01 — Schema Validation & Data Loading
- **Purpose:** Load 9 bảng CSV từ dataset Olist, kiểm tra tính đầy đủ schema (cột bắt buộc), ghi nhận số dòng gốc, tỷ lệ missing value và phân bổ order_status. Đảm bảo dữ liệu đầu vào có đủ cột cần thiết trước khi xử lý tiếp.
- **Phase IDs:** 1
- **Step IDs:** 1.1
- **Owned requirements:** FR-01, FR-02, FR-03
- **Inputs:** 9 file CSV từ dataset Olist
- **Outputs:** 9 DataFrame đã load vào memory, Báo cáo schema validation (số dòng, tỷ lệ missing value, phân bổ order_status)
- **Depends on:** N/A
- **Downstream consumers:** DM-02, DM-03
- **Invariants:**
  - Tất cả 9 bảng phải load thành công với schema đầy đủ
  - Báo cáo ghi rõ số dòng gốc từng bảng trước khi làm sạch
  - Không thay đổi dữ liệu gốc, chỉ đọc và validate

### DM-02 — Delivery Metrics Calculation
- **Purpose:** Chuẩn hóa timestamp (order_purchase_timestamp, order_estimated_delivery_date, order_delivered_customer_date) về kiểu datetime, loại đơn thiếu timestamp hoặc chưa giao, tính cột is_late và delivery_days. Tạo bảng orders_clean làm nền cho phân tích giao trễ.
- **Phase IDs:** 1
- **Step IDs:** 1.2
- **Owned requirements:** FR-03
- **Inputs:** DataFrame orders gốc từ DM-01
- **Outputs:** Bảng orders_clean (order_id, customer_id, order_status, order_purchase_timestamp, order_estimated_delivery_date, order_delivered_customer_date, is_late, delivery_days), Báo cáo validation: số đơn bị loại do thiếu timestamp, tỷ lệ giao trễ trên tập đơn hợp lệ
- **Depends on:** DM-01
- **Downstream consumers:** DM-03, DM-04, DM-05, DM-06
- **Invariants:**
  - is_late chỉ được tính cho đơn có order_status='delivered' và đủ cả hai timestamp
  - delivery_days = order_delivered_customer_date - order_purchase_timestamp (đơn vị: ngày)
  - Tỷ lệ giao trễ = (số đơn is_late = true) / (số đơn delivered có đủ timestamp)

### DM-03 — Revenue & Customer Aggregation
- **Purpose:** Tổng hợp order_payments theo order_id để tạo bảng order_revenue, nối orders với customers qua customer_id để lấy customer_unique_id, tính order_count, total_revenue, first_order_date, last_order_date theo customer_unique_id. Tạo bảng customer_summary và order_revenue làm nền cho phân tích khách hàng và doanh thu.
- **Phase IDs:** 1
- **Step IDs:** 1.3
- **Owned requirements:** FR-01, FR-02, FR-04
- **Inputs:** DataFrame order_payments từ DM-01, DataFrame orders_clean từ DM-02, DataFrame customers từ DM-01
- **Outputs:** Bảng order_revenue (order_id, total_payment_value), Bảng customer_summary (customer_unique_id, order_count, total_revenue, first_order_date, last_order_date), Báo cáo validation: tổng payment_value khớp với gốc, tổng số customer_unique_id duy nhất
- **Depends on:** DM-01, DM-02
- **Downstream consumers:** DM-04, DM-05, DM-06
- **Invariants:**
  - order_revenue.total_payment_value = SUM(order_payments.payment_value) GROUP BY order_id
  - customer_summary group theo customer_unique_id (không dùng customer_id từ bảng orders)
  - Tổng payment_value từ order_revenue phải bằng tổng payment_value từ order_payments gốc (cho đơn đã giao)

### DM-04 — Baseline Metrics Calculation
- **Purpose:** Tính các chỉ số nền tảng tổng thể (tỷ lệ mua lặp lại, tỷ lệ giao trễ, doanh thu theo tháng và danh mục) làm mốc so sánh cho phân tích phức tạp. Đảm bảo baseline được tính đúng trước khi phân tích đa chiều.
- **Phase IDs:** 2
- **Step IDs:** 2.1, 2.2, 2.3
- **Owned requirements:** FR-01, FR-02, FR-03, FR-04, FR-06
- **Inputs:** Bảng customer_summary từ DM-03, Bảng orders_clean từ DM-02, Bảng order_revenue từ DM-03, DataFrame order_items từ DM-01
- **Outputs:** Tỷ lệ mua lặp lại tổng thể (%), Thời gian mua lại trung bình (ngày), Tỷ lệ giao trễ tổng thể (%), Số ngày trễ trung bình, Doanh thu theo tháng, Tốc độ tăng trưởng trung bình (%), Top 5 danh mục sản phẩm theo doanh thu, Tỷ lệ phí vận chuyển trên tổng doanh thu
- **Depends on:** DM-02, DM-03
- **Downstream consumers:** N/A
- **Invariants:**
  - Tỷ lệ mua lặp lại = (số customer_unique_id có order_count ≥ 2) / (tổng số customer_unique_id)
  - Tỷ lệ giao trễ chỉ tính trên đơn có order_status='delivered' và đủ timestamp
  - Doanh thu theo tháng được tổng hợp từ order_revenue nối với orders.order_purchase_timestamp

### DM-05 — Multi-Dimensional Analysis
- **Purpose:** Xây dựng các bảng phân tích đa chiều: cohort retention theo tháng đầu mua, late delivery segmentation theo bang/danh mục/seller, revenue decomposition theo tháng/danh mục/bang/phương thức thanh toán, correlation matrix giữa late_days, review_score, order_revenue và repeat_purchase. Tạo nền tảng cho insight hành động.
- **Phase IDs:** 3
- **Step IDs:** 3.1, 3.2, 3.3
- **Owned requirements:** FR-01, FR-02, FR-03, FR-04, FR-05, FR-06, FR-07
- **Inputs:** Bảng customer_summary từ DM-03, Bảng orders_clean từ DM-02, Bảng order_revenue từ DM-03, DataFrame order_reviews từ DM-01, DataFrame sellers từ DM-01, DataFrame products từ DM-01
- **Outputs:** Bảng cohort retention matrix (cohort_month, age_month, retention_rate), Bảng CLV theo cohort, Phân bổ khách hàng theo số đơn (1, 2, 3+), Thời gian mua lại trung bình, Bảng late_rate theo bang/danh mục/seller (top 10-15), Bảng segmentation theo mức độ trễ và review_score, Bảng so sánh repeat_rate giữa nhóm first-order experience (on-time vs late vs canceled), Bảng revenue_trend theo tháng (total_revenue, order_count, AOV, MoM_growth, freight_ratio), Bảng top danh mục/bang/payment_type, Ma trận tương quan giữa late_days, review_score, order_revenue, repeat_purchase với biến kiểm soát, Bảng partial correlation coefficients
- **Depends on:** DM-02, DM-03
- **Downstream consumers:** DM-06
- **Invariants:**
  - Cohort retention group theo first_order_date (tháng) và tính retention theo tháng tiếp theo
  - Late delivery segmentation phải ưu tiên dùng customer_state và customer_city, không phân tích chi tiết theo zip code
  - Revenue decomposition phải tách rõ product_value và freight_value
  - Correlation analysis phải có biến kiểm soát (tháng mua, danh mục, bang)

### DM-06 — Validation & Quality Assurance
- **Purpose:** Xác minh tính chính xác của các chỉ số nền tảng (khách hàng, doanh thu, giao trễ), kiểm tra tính nhất quán logic tính toán, so sánh insight đa chiều với baseline để xác nhận giá trị gia tăng, và xác minh mỗi khuyến nghị đều có bằng chứng định lượng từ insight.
- **Phase IDs:** 4
- **Step IDs:** 4.1, 4.2, 4.3
- **Owned requirements:** FR-01, FR-02, FR-03, FR-06, FR-08, FR-09, FR-10
- **Inputs:** Bảng customer_summary từ DM-03, Bảng order_revenue từ DM-03, Bảng orders_clean từ DM-02, DataFrame customers gốc từ DM-01, DataFrame order_payments gốc từ DM-01, Cohort retention matrix từ DM-05, Risk segmentation table từ DM-05, Revenue decomposition từ DM-05, Baseline metrics từ DM-04
- **Outputs:** Validation report với ba phần: (1) Số customer_unique_id duy nhất (expected vs actual), (2) Tổng doanh thu (expected vs actual, delta), (3) Tỷ lệ giao trễ (số đơn đã giao có đủ timestamp, số đơn trễ, tỷ lệ %, số đơn bị loại), Baseline comparison report: (1) Cohort retention vs baseline, (2) Risk segmentation vs baseline, (3) Revenue decomposition vs baseline với p-value và effect size, Traceability matrix (recommendation_id → insight_id → evidence_summary), Danh sách khuyến nghị đạt chuẩn (có đầy đủ bằng chứng + phân loại) vs danh sách khuyến nghị bị loại
- **Depends on:** DM-02, DM-03, DM-05
- **Downstream consumers:** N/A
- **Invariants:**
  - Tổng customer_unique_id phải khớp giữa customer_summary và bảng customers gốc sau khi nối với orders
  - Tổng doanh thu từ order_revenue phải bằng tổng payment_value từ order_payments gốc (cho đơn đã giao)
  - Insight phức tạp phải có chênh lệch có ý nghĩa so với baseline (p < 0.05 hoặc effect size ≥ 5%)
  - Mỗi khuyến nghị phải truy ngược được về ít nhất một insight có bằng chứng định lượng

---

## 7. CODEBASE ĐẦY ĐỦ CHI TIẾT (EXECUTION BLUEPRINT)

## PART A: Codebase Structure
```text
project_root/
├── config/
│   ├── settings.py
│   └── __init__.py
├── utils/
│   ├── logger.py
│   ├── datetime_utils.py
│   ├── stats_utils.py
│   └── __init__.py
├── data_ingestion/
│   ├── loader.py
│   ├── schema_validator.py
│   └── __init__.py
├── data_preparation/
│   ├── datetime_normalizer.py
│   ├── delivery_metrics.py
│   └── __init__.py
├── data_aggregation/
│   ├── revenue_aggregator.py
│   ├── customer_aggregator.py
│   └── __init__.py
├── baseline_metrics/
│   ├── retention_metrics.py
│   ├── delivery_metrics.py
│   ├── revenue_metrics.py
│   └── __init__.py
├── analysis/
│   ├── cohort_analysis.py
│   ├── delivery_analysis.py
│   ├── revenue_analysis.py
│   └── __init__.py
├── validation/
│   ├── metrics_validator.py
│   ├── baseline_comparator.py
│   ├── traceability_checker.py
│   └── __init__.py
├── reporting/
│   ├── report_builder.py
│   ├── insight_formatter.py
│   └── __init__.py
├── main.py
├── requirements.txt
└── README.md
```

## PART A.1: Codebase Modules
### `CB-01` — `data_ingestion/`
- **Design module:** DM-01
- **Responsibility:** Load 9 bảng CSV từ dataset Olist, validate schema (kiểm tra cột bắt buộc), ghi nhận số dòng gốc, tỷ lệ missing value và phân bổ order_status. Đảm bảo dữ liệu đầu vào có đủ cột cần thiết trước khi xử lý tiếp.
- **Owned requirements:** FR-01, FR-02, FR-03
- **Files:**
  - `data_ingestion/loader.py` — Load 9 file CSV (orders, order_items, order_payments, customers, sellers, products, order_reviews, geolocation, product_category_name_translation) vào DataFrame bằng pandas.read_csv(). Return dict[str, pd.DataFrame].
  - `data_ingestion/schema_validator.py` — Validate schema: kiểm tra cột bắt buộc theo data contract (orders: order_id, customer_id, order_status, order_purchase_timestamp, order_estimated_delivery_date, order_delivered_customer_date; customers: customer_id, customer_unique_id; order_payments: order_id, payment_value; v.v.). Return validation report: số dòng gốc, tỷ lệ missing value theo cột, phân bổ order_status.
  - `data_ingestion/__init__.py` — Export load_datasets() và validate_schema() cho downstream modules.

### `CB-02` — `data_preparation/`
- **Design module:** DM-02
- **Responsibility:** Chuẩn hóa timestamp (order_purchase_timestamp, order_estimated_delivery_date, order_delivered_customer_date) về kiểu datetime, loại đơn thiếu timestamp hoặc chưa giao, tính cột is_late và delivery_days. Tạo bảng orders_clean làm nền cho phân tích giao trễ.
- **Owned requirements:** FR-03
- **Files:**
  - `data_preparation/datetime_normalizer.py` — Chuẩn hóa order_purchase_timestamp, order_estimated_delivery_date, order_delivered_customer_date về pd.datetime, extract date (dt.date). Loại đơn thiếu timestamp hoặc order_status != 'delivered'. Return orders DataFrame với các cột datetime chuẩn hóa.
  - `data_preparation/delivery_metrics.py` — Tính cột is_late (boolean: order_delivered_customer_date > order_estimated_delivery_date), delivery_days (order_delivered_customer_date - order_purchase_timestamp), estimated_days (order_estimated_delivery_date - order_purchase_timestamp). Return orders_clean (order_id, customer_id, order_status, order_purchase_timestamp, order_estimated_delivery_date, order_delivered_customer_date, is_late, delivery_days). Ghi validation report: số đơn bị loại do thiếu timestamp, tỷ lệ giao trễ.
  - `data_preparation/__init__.py` — Export prepare_orders_clean() cho downstream modules.

### `CB-03` — `data_aggregation/`
- **Design module:** DM-03
- **Responsibility:** Tổng hợp order_payments theo order_id để tạo bảng order_revenue, nối orders với customers qua customer_id để lấy customer_unique_id, tính order_count, total_revenue, first_order_date, last_order_date theo customer_unique_id. Tạo bảng customer_summary và order_revenue làm nền cho phân tích khách hàng và doanh thu.
- **Owned requirements:** FR-01, FR-02, FR-04
- **Files:**
  - `data_aggregation/revenue_aggregator.py` — Tổng hợp order_payments theo order_id: groupby('order_id').agg({'payment_value': 'sum'}). Tách product_value và freight_value nếu có trong order_payments hoặc tính từ order_items. Return order_revenue (order_id, total_payment_value, product_value, freight_value). Validate: sum(order_revenue.total_payment_value) == sum(order_payments.payment_value).
  - `data_aggregation/customer_aggregator.py` — Nối orders_clean với customers qua customer_id để lấy customer_unique_id. Groupby customer_unique_id: tính order_count, total_revenue (nối với order_revenue), first_order_date (min order_purchase_timestamp), last_order_date (max order_purchase_timestamp), is_repeat (order_count >= 2). Return customer_summary (customer_unique_id, order_count, total_revenue, first_order_date, last_order_date, is_repeat). Validate: COUNT DISTINCT customer_unique_id khớp với số khách hàng thật.
  - `data_aggregation/__init__.py` — Export aggregate_revenue() và aggregate_customers() cho downstream modules.

### `CB-04` — `baseline_metrics/`
- **Design module:** DM-04
- **Responsibility:** Tính các chỉ số nền tảng tổng thể (tỷ lệ mua lặp lại, tỷ lệ giao trễ, doanh thu theo tháng và danh mục) làm mốc so sánh cho phân tích phức tạp. Đảm bảo baseline được tính đúng trước khi phân tích đa chiều.
- **Owned requirements:** FR-01, FR-02, FR-03, FR-04, FR-06
- **Files:**
  - `baseline_metrics/retention_metrics.py` — Tính tỷ lệ mua lặp lại tổng thể: (số customer_unique_id có order_count >= 2) / (tổng customer_unique_id). Tính thời gian mua lại trung bình: (last_order_date - first_order_date) trên tập is_repeat=True. Return dict: {'repeat_rate': float, 'avg_repurchase_days': float}.
  - `baseline_metrics/delivery_metrics.py` — Tính tỷ lệ giao trễ tổng thể: (số đơn is_late=True) / (số đơn delivered có đủ timestamp). Tính số ngày trễ trung bình: (order_delivered_customer_date - order_estimated_delivery_date) trên tập is_late=True. Return dict: {'late_rate': float, 'avg_late_days': float, 'total_delivered': int, 'total_late': int}.
  - `baseline_metrics/revenue_metrics.py` — Tính doanh thu theo tháng: groupby order_purchase_timestamp.dt.to_period('M'), sum(total_payment_value). Tính tốc độ tăng trưởng MoM trung bình. Tính top 5 danh mục sản phẩm theo doanh thu (nối order_items với products, groupby product_category_name). Tính tỷ lệ phí vận chuyển: sum(freight_value) / sum(total_payment_value). Return dict: {'revenue_by_month': pd.DataFrame, 'avg_growth_rate': float, 'top_categories': pd.DataFrame, 'freight_ratio': float}.
  - `baseline_metrics/__init__.py` — Export calculate_baseline_metrics() tổng hợp tất cả chỉ số nền.

### `CB-05` — `analysis/`
- **Design module:** DM-05
- **Responsibility:** Xây dựng các bảng phân tích đa chiều: cohort retention theo tháng đầu mua, late delivery segmentation theo bang/danh mục/seller, revenue decomposition theo tháng/danh mục/bang/phương thức thanh toán, correlation matrix giữa late_days, review_score, order_revenue và repeat_purchase. Tạo nền tảng cho insight hành động.
- **Owned requirements:** FR-01, FR-02, FR-03, FR-04, FR-05, FR-06, FR-07
- **Files:**
  - `analysis/cohort_analysis.py` — Tạo cohort retention matrix: cohort = first_order_date.dt.to_period('M'), age_month = (order_purchase_timestamp - first_order_date) / 30 days. Groupby (cohort, age_month): tính retention_rate = số customer_unique_id active / số customer_unique_id trong cohort ban đầu. Tính CLV theo cohort: sum(total_revenue) / số customer_unique_id trong cohort. Phân bổ khách hàng theo số đơn (1, 2, 3+). Return: cohort_retention (cohort_month, age_month, retention_rate), cohort_clv (cohort_month, clv), customer_distribution (order_count_bucket, customer_count).
  - `analysis/delivery_analysis.py` — Phân tích giao trễ theo bang/danh mục/seller: nối orders_clean với customers (customer_state), order_items (product_id → products → product_category_name), sellers (seller_id → seller_state). Groupby (customer_state / product_category_name / seller_id): tính late_rate, avg_late_days, order_count. Lấy top 10-15 theo late_rate. Segmentation theo mức độ trễ (on-time, 1-3 days late, 4-7 days late, >7 days late) và review_score (nối với order_reviews). So sánh repeat_rate giữa nhóm first-order experience (on-time vs late vs canceled). Return: late_by_state, late_by_category, late_by_seller, segmentation_table, first_order_experience_impact.
  - `analysis/revenue_analysis.py` — Phân tích revenue decomposition: groupby (tháng, danh mục, bang, phương thức thanh toán). Tính total_revenue, order_count, AOV (avg order value), MoM_growth, freight_ratio. Correlation matrix: tính pearson correlation giữa late_days (delivery_days - estimated_days), review_score, order_revenue, is_repeat. Return: revenue_trend (month, total_revenue, order_count, AOV, MoM_growth, freight_ratio), revenue_by_category, revenue_by_state, revenue_by_payment_type, correlation_matrix.
  - `analysis/__init__.py` — Export run_multidimensional_analysis() tổng hợp tất cả phân tích đa chiều.

### `CB-06` — `validation/`
- **Design module:** DM-06
- **Responsibility:** Xác minh tính chính xác của các chỉ số nền tảng (khách hàng, doanh thu, giao trễ), kiểm tra tính nhất quán logic tính toán, so sánh insight đa chiều với baseline để xác nhận giá trị gia tăng, và xác minh mỗi khuyến nghị đều có bằng chứng định lượng từ insight.
- **Owned requirements:** FR-01, FR-02, FR-03, FR-06, FR-08, FR-09, FR-10
- **Files:**
  - `validation/metrics_validator.py` — Validate chỉ số nền: (1) COUNT DISTINCT customer_unique_id từ customer_summary == COUNT DISTINCT customer_unique_id từ customers gốc (nối qua orders). (2) sum(order_revenue.total_payment_value) == sum(order_payments.payment_value) cho tập đơn đã giao. (3) Tỷ lệ giao trễ: đếm riêng (order_status='delivered' AND đủ timestamp) vs (is_late=True). Return validation_report: expected vs actual, delta, pass/fail cho từng chỉ số.
  - `validation/baseline_comparator.py` — So sánh insight đa chiều với baseline: (1) Cohort retention vs baseline repeat_rate. (2) Risk segmentation (late_by_state, late_by_category) vs baseline late_rate. (3) Revenue decomposition (by category, by state) vs baseline revenue_by_month. Tính p-value (t-test hoặc chi-square) và effect size (Cohen's d). Return baseline_comparison_report: insight_id, baseline_value, actual_value, p_value, effect_size, significance.
  - `validation/traceability_checker.py` — Xác minh mỗi khuyến nghị (từ AT-004) có gắn với ít nhất một insight (từ AT-003). Tạo traceability matrix: recommendation_id → insight_id → evidence_summary. Phân loại khuyến nghị: đạt chuẩn (có đầy đủ bằng chứng + phân loại impact×feasibility×risk) vs bị loại (thiếu bằng chứng). Return traceability_matrix, approved_recommendations, rejected_recommendations.
  - `validation/__init__.py` — Export run_validation() tổng hợp tất cả validation checks.

### `CB-07` — `reporting/`
- **Design module:** None
- **Responsibility:** Biên soạn báo cáo insight cuối cùng với cấu trúc: tóm tắt điều hành, phương pháp và data quality, phân tích 3 trục, insight chính (6-10 insight), ma trận khuyến nghị, phụ lục kỹ thuật. Đảm bảo báo cáo đáp ứng đủ 3 success criteria và có thể sử dụng trực tiếp để ra quyết định.
- **Owned requirements:** FR-04, FR-06, FR-07, FR-08, FR-09, FR-10, FR-12
- **Files:**
  - `reporting/report_builder.py` — Tổng hợp tất cả output từ CB-04 (baseline), CB-05 (multi-dimensional analysis), CB-06 (validation) thành báo cáo văn bản có cấu trúc: (1) Executive summary, (2) Phương pháp + data quality, (3) Phân tích 3 trục (retention, delivery, revenue), (4) Insight chính (6-10 insight), (5) Ma trận khuyến nghị (impact×feasibility×risk), (6) Phụ lục kỹ thuật (công thức, validation report, giả định, giới hạn). Ghi rõ license: 'Brazilian E-Commerce Public Dataset by Olist, Kaggle, CC BY-NC-SA 4.0'.
  - `reporting/insight_formatter.py` — Format insight theo chuẩn FR-06: mỗi insight kèm bằng chứng định lượng cụ thể (tỷ lệ %, số tuyệt đối, xu hướng thời gian). Format khuyến nghị theo FR-07: phân loại impact/feasibility/risk, highlight 3-5 khuyến nghị ưu tiên cao.
  - `reporting/__init__.py` — Export generate_final_report() cho main pipeline.

### `CB-08` — `config/`
- **Design module:** None
- **Responsibility:** Quản lý cấu hình toàn cục: đường dẫn 9 file CSV, schema cột bắt buộc, ngưỡng validation, danh sách cột cần thiết cho từng bảng. Centralize config để dễ maintain.
- **Owned requirements:** N/A
- **Files:**
  - `config/settings.py` — Define constants: CSV_PATHS (dict mapping tên bảng → đường dẫn file), REQUIRED_COLUMNS (dict mapping tên bảng → list cột bắt buộc), VALIDATION_THRESHOLDS (missing_rate_threshold, late_rate_threshold). Export settings object.
  - `config/__init__.py` — Export settings cho toàn project.

### `CB-09` — `utils/`
- **Design module:** None
- **Responsibility:** Utility functions dùng chung: logging, error handling, file I/O helper, datetime helper, statistical helper (correlation, t-test, Cohen's d).
- **Owned requirements:** N/A
- **Files:**
  - `utils/logger.py` — Setup logging: console + file handler, format rõ ràng (timestamp, level, message). Export get_logger().
  - `utils/datetime_utils.py` — Helper functions: parse_date(), normalize_to_date(), calculate_days_between(). Handle edge cases (None, invalid format).
  - `utils/stats_utils.py` — Statistical helpers: calculate_correlation_matrix(), t_test(), cohens_d(), confidence_interval(). Dùng scipy.stats hoặc numpy.
  - `utils/__init__.py` — Export tất cả utils cho toàn project.

### `CB-10` — `./`
- **Design module:** None
- **Responsibility:** Entry point chính: orchestrate toàn bộ pipeline từ ingestion → preparation → aggregation → baseline → analysis → validation → reporting. Đảm bảo dependency chạy đúng thứ tự.
- **Owned requirements:** N/A
- **Files:**
  - `main.py` — Main pipeline: (1) Load datasets (CB-01), (2) Prepare orders_clean (CB-02), (3) Aggregate revenue & customers (CB-03), (4) Calculate baseline (CB-04), (5) Run multi-dimensional analysis (CB-05), (6) Validate metrics & insights (CB-06), (7) Generate final report (CB-07). Log progress và error handling. Entry point: python main.py.
  - `requirements.txt` — List dependencies: pandas>=2.0.0, numpy>=1.24.0, scipy>=1.10.0, haversine>=2.8.0, duckdb>=0.9.0 (hoặc sqlite3 built-in). Optional: jupyter, matplotlib, seaborn (nếu cần visualization).
  - `README.md` — Hướng dẫn setup: cài dependencies, download dataset Olist từ Kaggle, cấu hình đường dẫn CSV trong config/settings.py, chạy pipeline python main.py. Ghi rõ license CC BY-NC-SA 4.0 và giới hạn phi thương mại.

### Folder: `data_ingestion/`

#### File: `data_ingestion/loader.py`
```python
def load_datasets:
    # Responsibility: Load 9 bảng CSV từ dataset Olist (orders, customers, order_payments, order_items, sellers, products, geolocation, order_reviews, product_category_name_translation) vào dict[str, pd.DataFrame]. Return dict mapping tên bảng thành DataFrame để downstream modules truy cập.
    # Task Execution
        # Duyệt 9 tên file CSV theo mapping cố định (olist_orders_dataset.csv → 'orders', ...)
        # Gọi pd.read_csv() cho từng file với encoding='utf-8', fallback sang 'latin-1' nếu UnicodeDecodeError
        # Validate mỗi DataFrame có ít nhất 1 dòng; log warning nếu file rỗng
        # Return dict[str, pd.DataFrame] với 9 cặp key-value
    #/Task Execution
    # Input contract: Nhận data_dir (str hoặc Path) trỏ đến thư mục chứa 9 file CSV; Mỗi file CSV phải có header dòng đầu tiên; Encoding UTF-8 hoặc Latin-1 cho file product_category_name_translation
    # Output contract: Return dict[str, pd.DataFrame] với 9 keys: 'orders', 'customers', 'order_payments', 'order_items', 'sellers', 'products', 'geolocation', 'order_reviews', 'product_category_name_translation'; Mỗi DataFrame giữ nguyên schema gốc (chưa parse datetime), tất cả cột dạng object hoặc numeric; Raise FileNotFoundError nếu thiếu bất kỳ file nào trong 9 file
    # Semantic invariants: Không parse datetime hoặc transform dữ liệu tại bước load; giữ nguyên raw CSV; Số dòng mỗi DataFrame phải > 0 (dataset không rỗng); Các cột timestamp (order_purchase_timestamp, order_estimated_delivery_date, order_delivered_customer_date) được load dạng string, chưa convert sang datetime
    # Forbidden shortcuts: Không drop NaN hoặc filter rows tại bước load; validation xảy ra ở step 1.1 sau load; Không merge/join các bảng tại loader; mỗi bảng độc lập; Không cache DataFrame vào disk; load mỗi lần chạy để đảm bảo data mới nhất
```
> **`load_datasets`** | **Pipeline:** Phase 1 → Step 1.1 | **Design module:** DM-01 | **Addresses:** FR-01, FR-02, FR-03 | **Depends on:** *(không có)* | **Called by:** data_ingestion/schema_validator.py::validate_schema


#### File: `data_ingestion/schema_validator.py`
```python
def validate_schema:
    # Responsibility: Validate schema của 9 bảng: kiểm tra cột bắt buộc tồn tại (orders: order_id, customer_id, order_status, order_purchase_timestamp, order_estimated_delivery_date, order_delivered_customer_date; customers: customer_id, customer_unique_id; order_payments: order_id, payment_value; ...), tính tỷ lệ missing value cho cột quan trọng, phân bổ order_status. Return validation report dict.
    # Task Execution
        # Định nghĩa dict REQUIRED_COLUMNS = {'orders': ['order_id', 'customer_id', ...], 'customers': [...], ...}
        # Duyệt từng bảng: check set(df.columns).issuperset(REQUIRED_COLUMNS[table_name]); raise ValueError nếu thiếu
        # Tính missing_rates = {col: df[col].isna().mean() for col in required_cols}
        # Với bảng orders: tính order_status_dist = df['order_status'].value_counts().to_dict()
        # Aggregate thành validation_report dict và return
    #/Task Execution
    # Input contract: Nhận datasets dict[str, pd.DataFrame] từ load_datasets(); Mỗi DataFrame đã load đầy đủ, chưa bị filter; Các cột timestamp vẫn dạng string
    # Output contract: Return validation_report dict chứa: {'orders': {'row_count': int, 'missing_rates': {col: float}, 'order_status_dist': {status: int}}, 'customers': {...}, ...}; missing_rates: tỷ lệ NaN của từng cột bắt buộc (0.0 đến 1.0); Raise ValueError nếu thiếu cột bắt buộc hoặc bảng rỗng
    # Semantic invariants: Không modify DataFrame gốc; chỉ đọc và tính metric; Tất cả cột bắt buộc theo data contract phải tồn tại (không chấp nhận alias hoặc cột gần đúng); order_status_dist chỉ tính trên bảng orders, phải có ít nhất status 'delivered'
    # Forbidden shortcuts: Không fill NaN hoặc impute missing value; chỉ report tỷ lệ; Không drop rows tại validation; downstream step sẽ filter; Không assume default value cho missing timestamp (VD: assume today nếu order_delivered_customer_date null)
```
> **`validate_schema`** | **Pipeline:** Phase 1 → Step 1.1 | **Design module:** DM-01 | **Addresses:** FR-01, FR-02, FR-03 | **Depends on:** data_ingestion/loader.py::load_datasets | **Called by:** data_preparation/datetime_normalizer.py::prepare_orders_clean


### Folder: `data_preparation/`

#### File: `data_preparation/datetime_normalizer.py`
```python
def normalize_timestamps:
    # Responsibility: Chuẩn hóa order_purchase_timestamp, order_estimated_delivery_date, order_delivered_customer_date về pd.Timestamp (datetime64[ns]), extract date (dt.date) để so sánh SLA. Loại đơn có order_status != 'delivered' hoặc thiếu timestamp quan trọng. Return orders DataFrame đã clean.
    # Task Execution
        # Parse 3 cột timestamp bằng pd.to_datetime(df[col], errors='coerce', utc=False) để giữ nguyên timezone gốc
        # Filter df[df['order_status'] == 'delivered']; log số dòng bị loại
        # Filter df[df['order_estimated_delivery_date'].notna() & df['order_delivered_customer_date'].notna()]; log thêm
        # Return df_normalized với 3 cột timestamp dạng datetime64[ns]
    #/Task Execution
    # Input contract: Nhận orders DataFrame từ load_datasets(), chưa parse datetime; Các cột timestamp dạng string ISO 8601 hoặc format phổ biến; Cột order_status có giá trị 'delivered', 'canceled', 'shipped', ...
    # Output contract: Return orders_normalized DataFrame với 3 cột timestamp đã parse thành pd.Timestamp (UTC-aware hoặc naive tùy input); Chỉ giữ rows có order_status == 'delivered' AND order_estimated_delivery_date NOT NULL AND order_delivered_customer_date NOT NULL; Ghi log số dòng bị loại do thiếu timestamp hoặc chưa giao
    # Semantic invariants: Không fill NaN timestamp; chỉ loại row thiếu; Không chuyển timezone nếu input naive (giữ nguyên naive); nếu có timezone thì chuẩn hóa về UTC; order_purchase_timestamp luôn <= order_estimated_delivery_date <= order_delivered_customer_date (validation ở step sau)
    # Forbidden shortcuts: Không assume giá trị mặc định cho timestamp missing (VD: sử dụng today hoặc mean); Không parse timestamp bằng custom regex; dùng pd.to_datetime() với errors='coerce'; Không giữ đơn 'canceled' hoặc 'shipped' để tính is_late; chỉ 'delivered' hợp lệ
```
> **`normalize_timestamps`** | **Pipeline:** Phase 1 → Step 1.2 | **Design module:** DM-02 | **Addresses:** FR-03 | **Depends on:** data_ingestion/loader.py::load_datasets, data_ingestion/schema_validator.py::validate_schema | **Called by:** data_preparation/delivery_metrics.py::calculate_delivery_metrics


#### File: `data_preparation/delivery_metrics.py`
```python
def calculate_delivery_metrics:
    # Responsibility: Tính cột is_late (boolean: order_delivered_customer_date > order_estimated_delivery_date), delivery_days (int: khoảng ngày từ order_purchase_timestamp đến order_delivered_customer_date), estimated_days (int: từ purchase đến estimated). Thêm 3 cột mới vào orders DataFrame và return orders_clean.
    # Task Execution
        # Tính df['is_late'] = (df['order_delivered_customer_date'].dt.date > df['order_estimated_delivery_date'].dt.date).astype(bool)
        # Tính df['delivery_days'] = (df['order_delivered_customer_date'] - df['order_purchase_timestamp']).dt.days
        # Tính df['estimated_days'] = (df['order_estimated_delivery_date'] - df['order_purchase_timestamp']).dt.days
        # Validate delivery_days >= 0 và estimated_days >= 0; log warning nếu vi phạm
        # Return orders_clean với 3 cột mới
    #/Task Execution
    # Input contract: Nhận orders_normalized DataFrame từ normalize_timestamps() với 3 cột timestamp đã parse; Tất cả rows đều có order_status == 'delivered' và timestamp NOT NULL; Timestamp đã ở dạng pd.Timestamp (datetime64[ns])
    # Output contract: Return orders_clean DataFrame với 3 cột mới: is_late (bool), delivery_days (int), estimated_days (int); is_late = True nếu order_delivered_customer_date.date() > order_estimated_delivery_date.date(); delivery_days = (order_delivered_customer_date - order_purchase_timestamp).days; estimated_days tương tự
    # Semantic invariants: is_late chỉ so sánh DATE (không so sánh giờ/phút); extract .date() trước khi so sánh; delivery_days và estimated_days phải >= 0 (không có đơn giao trước ngày mua); flag warning nếu âm; Tỷ lệ giao trễ = is_late.mean() phải được ghi vào validation report
    # Forbidden shortcuts: Không so sánh timestamp trực tiếp mà không extract date; giờ giao có thể gây sai lệch; Không round delivery_days về số nguyên bằng .round(); dùng .days của timedelta; Không tính is_late dựa trên delivery_days > estimated_days; phải so sánh trực tiếp hai cột delivered vs estimated
```
> **`calculate_delivery_metrics`** | **Pipeline:** Phase 1 → Step 1.2 | **Design module:** DM-02 | **Addresses:** FR-03 | **Depends on:** data_preparation/datetime_normalizer.py::normalize_timestamps | **Called by:** data_aggregation/customer_aggregator.py::aggregate_customers


### Folder: `data_aggregation/`

#### File: `data_aggregation/revenue_aggregator.py`
```python
def aggregate_revenue:
    # Responsibility: Tổng hợp order_payments theo order_id: groupby('order_id').agg({'payment_value': 'sum'}). Validation: tổng payment_value khớp với bảng gốc. Return order_revenue DataFrame (order_id, total_payment_value).
    # Task Execution
        # Validate payment_value >= 0; log warning nếu có negative và convert thành 0
        # Groupby order_id: order_revenue = order_payments.groupby('order_id', as_index=False).agg({'payment_value': 'sum'}).rename(columns={'payment_value': 'total_payment_value'})
        # Validation: assert abs(order_revenue['total_payment_value'].sum() - order_payments['payment_value'].sum()) < 0.01 (tolerance 1 cent)
        # Return order_revenue DataFrame
    #/Task Execution
    # Input contract: Nhận order_payments DataFrame từ load_datasets() với cột order_id, payment_value; payment_value dạng numeric (float hoặc int), có thể chứa NaN; Một order_id có thể có nhiều dòng payment (nhiều phương thức thanh toán)
    # Output contract: Return order_revenue DataFrame với 2 cột: order_id (index hoặc cột), total_payment_value (float); total_payment_value = SUM(payment_value) theo order_id; NaN được bỏ qua (skipna=True); Validation: assert order_revenue['total_payment_value'].sum() == order_payments['payment_value'].sum()
    # Semantic invariants: Không drop order_id có payment_value == 0 hoặc NULL; giữ lại và tính sum = 0 hoặc NaN; order_id là unique trong order_revenue (mỗi order chỉ 1 dòng); total_payment_value phải >= 0 (không có negative payment); flag warning nếu có
    # Forbidden shortcuts: Không tính doanh thu từ order_items (price, freight_value); chỉ dùng order_payments; Không fill NaN payment_value bằng 0 trước khi sum; groupby.sum(skipna=True) tự xử lý; Không merge với orders tại bước này; chỉ aggregate payments thuần túy
```
> **`aggregate_revenue`** | **Pipeline:** Phase 1 → Step 1.3 | **Design module:** DM-03 | **Addresses:** FR-02, FR-04 | **Depends on:** data_ingestion/loader.py::load_datasets | **Called by:** data_aggregation/customer_aggregator.py::aggregate_customers


#### File: `data_aggregation/customer_aggregator.py`
```python
def aggregate_customers:
    # Responsibility: Nối orders_clean với customers qua customer_id để lấy customer_unique_id, nối với order_revenue để lấy total_payment_value. Groupby customer_unique_id: tính order_count, total_revenue (sum payment), first_order_date (min purchase timestamp), last_order_date (max). Return customer_summary DataFrame.
    # Task Execution
        # Merge orders_clean với customers: orders_with_unique = orders_clean.merge(customers[['customer_id', 'customer_unique_id']], on='customer_id', how='left')
        # Merge orders_with_unique với order_revenue: orders_full = orders_with_unique.merge(order_revenue, on='order_id', how='left')
        # Groupby customer_unique_id: customer_summary = orders_full.groupby('customer_unique_id', as_index=False).agg({'order_id': 'count', 'total_payment_value': 'sum', 'order_purchase_timestamp': ['min', 'max']})
        # Rename columns: order_count, total_revenue, first_order_date, last_order_date; convert timestamp thành .date()
        # Validation: assert customer_summary['customer_unique_id'].nunique() == customers['customer_unique_id'].nunique()
        # Return customer_summary
    #/Task Execution
    # Input contract: Nhận orders_clean DataFrame từ calculate_delivery_metrics() với customer_id, order_purchase_timestamp; Nhận customers DataFrame từ load_datasets() với customer_id, customer_unique_id; Nhận order_revenue DataFrame từ aggregate_revenue() với order_id, total_payment_value
    # Output contract: Return customer_summary DataFrame với 5 cột: customer_unique_id (index hoặc cột), order_count (int), total_revenue (float), first_order_date (datetime.date), last_order_date (datetime.date); order_count = COUNT(order_id) per customer_unique_id; Validation: tổng số customer_unique_id duy nhất phải khớp với customers['customer_unique_id'].nunique()
    # Semantic invariants: Phải dùng customer_unique_id (không dùng customer_id từ orders); một customer_unique_id có thể có nhiều customer_id; first_order_date <= last_order_date; nếu chỉ 1 đơn thì first == last; total_revenue phải >= 0; nếu order không có payment thì total_revenue = 0 hoặc NaN (tùy merge)
    # Forbidden shortcuts: Không groupby customer_id từ orders; phải join customers trước để lấy customer_unique_id; Không tính doanh thu từ order_items; phải dùng order_revenue đã aggregate; Không drop customer có order_count = 1; giữ tất cả khách hàng kể cả mua 1 lần
```
> **`aggregate_customers`** | **Pipeline:** Phase 1 → Step 1.3 | **Design module:** DM-03 | **Addresses:** FR-01, FR-02, FR-04 | **Depends on:** data_preparation/delivery_metrics.py::calculate_delivery_metrics, data_ingestion/loader.py::load_datasets, data_aggregation/revenue_aggregator.py::aggregate_revenue | **Called by:** *(không có)*


### Folder: `baseline_metrics/`

#### File: `baseline_metrics/retention_metrics.py`
```python
def calculate_retention_baseline(customer_summary: pd.DataFrame) -> dict:
    # Responsibility: Tính tỷ lệ mua lặp lại tổng thể = (số customer_unique_id có order_count >= 2) / (tổng customer_unique_id). Tính thời gian mua lại trung bình (ngày) trên tập khách hàng mua lặp lại. Trả về dict với repeat_rate, avg_repurchase_days, one_time_customers, repeat_customers
    # Task Execution
        # Filter customer_summary.order_count >= 2 để tạo tập repeat_customers
        # Tính repeat_rate = len(repeat_customers) / len(customer_summary)
        # Tính avg_repurchase_days = (last_order_date - first_order_date).dt.days.mean() trên tập repeat
        # Validate: sum(one_time + repeat) = total unique customer_unique_id
    #/Task Execution
    # Input contract: customer_summary có index=customer_unique_id, cột order_count, first_order_date, last_order_date không NULL; first_order_date và last_order_date là pandas Timestamp hoặc datetime đã chuẩn hóa
    # Output contract: dict {'repeat_rate': float (%), 'avg_repurchase_days': float, 'one_time_count': int, 'repeat_count': int}; repeat_rate = (repeat_count / total_customers) * 100, avg_repurchase_days chỉ tính trên repeat_count > 0
    # Semantic invariants: one_time_count + repeat_count = tổng số customer_unique_id duy nhất trong customer_summary; avg_repurchase_days >= 0; nếu repeat_count = 0 thì trả NaN hoặc None
    # Forbidden shortcuts: Không dùng customer_id từ orders thay vì customer_unique_id; Không tính repurchase_days trên tập có order_count = 1 (last = first)
```
> **`calculate_retention_baseline`** | **Pipeline:** Phase 2 → Step 2.1 | **Design module:** DM-04 | **Addresses:** FR-01, FR-04 | **Depends on:** *(không có)* | **Called by:** calculate_baseline_metrics


#### File: `baseline_metrics/delivery_metrics.py`
```python
def calculate_delivery_baseline(orders_clean: pd.DataFrame) -> dict:
    # Responsibility: Tính tỷ lệ giao trễ tổng thể = (số đơn is_late=True) / (số đơn delivered có đủ timestamp). Tính số ngày trễ trung bình trên tập is_late=True. Báo cáo số đơn bị loại do thiếu timestamp hoặc chưa giao. Trả về dict với late_rate, avg_late_days, excluded_count
    # Task Execution
        # Filter orders_clean: order_status='delivered' AND order_delivered_customer_date NOT NULL AND order_estimated_delivery_date NOT NULL
        # Tính late_rate = (is_late=True).sum() / len(filtered_sample)
        # Tính avg_late_days = (order_delivered_customer_date - order_estimated_delivery_date).dt.days.mean() trên is_late=True
        # Tính excluded_count = len(orders_clean) - len(filtered_sample); validate excluded_count >= 0
    #/Task Execution
    # Input contract: orders_clean có cột order_status='delivered', order_delivered_customer_date, order_estimated_delivery_date, is_late (boolean); Chỉ tính trên đơn delivered có đủ cả hai timestamp (không NULL)
    # Output contract: dict {'late_rate': float (%), 'avg_late_days': float, 'late_count': int, 'on_time_count': int, 'excluded_count': int}; late_rate = (late_count / (late_count + on_time_count)) * 100; avg_late_days chỉ tính trên is_late=True
    # Semantic invariants: late_count + on_time_count = số đơn delivered có đủ timestamp (sample size cho tỷ lệ trễ); excluded_count = số đơn bị loại do thiếu timestamp hoặc order_status != 'delivered'
    # Forbidden shortcuts: Không tính is_late bằng Timestamp comparison trực tiếp (phải cast sang DATE); Không bao gồm đơn thiếu order_estimated_delivery_date vào mẫu tính late_rate
```
> **`calculate_delivery_baseline`** | **Pipeline:** Phase 2 → Step 2.2 | **Design module:** DM-04 | **Addresses:** FR-03, FR-04 | **Depends on:** *(không có)* | **Called by:** calculate_baseline_metrics


#### File: `baseline_metrics/revenue_metrics.py`
```python
def calculate_revenue_baseline(order_revenue: pd.DataFrame, orders_clean: pd.DataFrame, order_items: pd.DataFrame) -> dict:
    # Responsibility: Tổng hợp doanh thu theo tháng từ order_revenue nối với orders_clean (order_purchase_timestamp), tính tốc độ tăng trưởng MoM trung bình. Tính top 5 danh mục sản phẩm theo doanh thu (nối order_items với products). Tính tỷ lệ freight_value / total_payment_value. Trả về dict với monthly_revenue (DataFrame), avg_growth_rate, top5_categories, freight_ratio
    # Task Execution
        # Nối order_revenue với orders_clean theo order_id, filter order_status='delivered', tạo cột month = order_purchase_timestamp.dt.to_period('M')
        # Groupby month, sum(total_payment_value) → monthly_revenue; tính MoM growth rate = (month[i] - month[i-1]) / month[i-1], avg_growth_rate = mean(MoM)
        # Nối order_revenue với order_items theo order_id, groupby product_category_name, sum(total_payment_value), lấy top 5
        # Tính freight_ratio = sum(freight_value) / sum(total_payment_value); validate ratio <= 1
    #/Task Execution
    # Input contract: order_revenue có order_id (khóa chính), total_payment_value, product_value, freight_value đã aggregated từ order_payments; orders_clean có order_id, order_purchase_timestamp (datetime), order_status='delivered'; order_items có order_id, product_category_name; nối với order_revenue theo order_id (1-n relationship)
    # Output contract: dict {'monthly_revenue': pd.DataFrame(month, revenue), 'avg_growth_rate': float (%), 'top5_categories': list[tuple(category, revenue)], 'freight_ratio': float}; monthly_revenue có index=month (period), cột revenue=SUM(total_payment_value); top5_categories sắp xếp giảm dần theo revenue
    # Semantic invariants: SUM(monthly_revenue.revenue) = SUM(order_revenue.total_payment_value) cho tập đơn delivered; freight_ratio = SUM(freight_value) / SUM(total_payment_value) trên toàn bộ order_revenue
    # Forbidden shortcuts: Không lấy price từ order_items trước khi aggregate theo order_id (risk: nhân doanh thu); Không tính revenue từ order_items.price + freight_value mà phải từ order_revenue.total_payment_value đã tổng hợp
```
> **`calculate_revenue_baseline`** | **Pipeline:** Phase 2 → Step 2.3 | **Design module:** DM-04 | **Addresses:** FR-02, FR-04, FR-06 | **Depends on:** *(không có)* | **Called by:** calculate_baseline_metrics


#### File: `baseline_metrics/__init__.py`
```python
def calculate_baseline_metrics(customer_summary: pd.DataFrame, orders_clean: pd.DataFrame, order_revenue: pd.DataFrame, order_items: pd.DataFrame) -> dict:
    # Responsibility: Tổng hợp tất cả baseline metrics (retention, delivery, revenue) từ các module con. Validate tính nhất quán giữa các chỉ số (total customers, total orders, total revenue). Trả về dict kết hợp kết quả từ calculate_retention_baseline, calculate_delivery_baseline, calculate_revenue_baseline
    # Task Execution
        # Gọi calculate_retention_baseline(customer_summary) → retention_metrics
        # Gọi calculate_delivery_baseline(orders_clean) → delivery_metrics
        # Gọi calculate_revenue_baseline(order_revenue, orders_clean, order_items) → revenue_metrics
        # Validate: total_customers = len(customer_summary), total_orders = len(orders_clean), total_revenue = order_revenue.total_payment_value.sum()
        # Kết hợp kết quả vào dict tổng hợp và trả về
    #/Task Execution
    # Input contract: customer_summary từ DM-03/CB-03, orders_clean từ DM-02/CB-02, order_revenue từ DM-03/CB-03, order_items từ DM-01/CB-01; Tất cả DataFrame đã được làm sạch và validated theo data contract Phase 1
    # Output contract: dict {'retention': {...}, 'delivery': {...}, 'revenue': {...}, 'validation': {...}}; validation chứa cross-check: total_customers (từ customer_summary), total_orders (từ orders_clean), total_revenue (từ order_revenue)
    # Semantic invariants: total_customers từ retention = len(customer_summary.customer_unique_id.unique()); total_orders từ delivery + excluded_count <= len(orders_clean)
    # Forbidden shortcuts: Không bỏ qua validation cross-check giữa các module; Không tính baseline trên subset ngẫu nhiên (phải dùng toàn bộ dataset)
```
> **`calculate_baseline_metrics`** | **Pipeline:** Phase 2 → Entry point | **Design module:** DM-04 | **Addresses:** FR-01, FR-02, FR-03, FR-04, FR-06 | **Depends on:** calculate_retention_baseline, calculate_delivery_baseline, calculate_revenue_baseline | **Called by:** *(không có)*


### Folder: `analysis/`

#### File: `analysis/cohort_analysis.py`
```python
def compute_cohort_retention_matrix(customer_summary: pd.DataFrame, orders_clean: pd.DataFrame) -> pd.DataFrame:
    # Responsibility: Tạo cohort retention matrix: gán cohort_month từ first_order_date, tính age_month từ order_purchase_timestamp, groupby (cohort_month, age_month) để tính retention_rate = số customer_unique_id active / số customer_unique_id trong cohort ban đầu. Trả về bảng pivot với cohort_month theo hàng, age_month theo cột, retention_rate làm giá trị.
    # Task Execution
        # Merge orders_clean với customer_summary on customer_unique_id, tính cohort_month = first_order_date.dt.to_period('M'), age_month = ((order_purchase_timestamp - first_order_date).dt.days / 30).astype(int)
        # Groupby (cohort_month, age_month): count distinct customer_unique_id làm active_customers; lấy cohort_size từ customer_summary group by cohort_month
        # Tính retention_rate = active_customers / cohort_size, pivot thành ma trận (cohort_month × age_month), trả về DataFrame
    #/Task Execution
    # Input contract: customer_summary phải có customer_unique_id, first_order_date (datetime, không null), order_count; orders_clean phải có customer_unique_id, order_purchase_timestamp (datetime, không null); Mỗi customer_unique_id trong orders_clean phải có mapping tới customer_summary
    # Output contract: DataFrame với multi-index (cohort_month, age_month) hoặc pivot table; retention_rate trong khoảng [0, 1], không null; Cohort_month phải sắp xếp tăng dần, age_month bắt đầu từ 0
    # Semantic invariants: retention_rate(cohort, age=0) = 1.0 (toàn bộ khách hàng active trong tháng đầu); retention_rate(cohort, age_k) ≤ retention_rate(cohort, age_j) với k > j (monotonic decrease); Tổng số customer_unique_id duy nhất trong output phải khớp với customer_summary
    # Forbidden shortcuts: Không dùng customer_id từ orders thay cho customer_unique_id; Không tính retention từ order_count mà không kiểm tra order_purchase_timestamp; Không skip validation cho first_order_date null hoặc orders ngoài time range

def compute_clv_by_cohort(customer_summary: pd.DataFrame, order_revenue: pd.DataFrame) -> pd.DataFrame:
    # Responsibility: Tính CLV (Customer Lifetime Value) theo cohort: merge customer_summary với order_revenue để tính total_revenue per customer, gán cohort_month từ first_order_date, groupby cohort_month để tính mean_clv, median_clv, percentile_90_clv, cohort_size. Trả về bảng CLV summary theo cohort.
    # Task Execution
        # Join orders_clean với order_revenue on order_id, groupby customer_unique_id: sum payment_value làm total_clv
        # Merge với customer_summary on customer_unique_id, gán cohort_month = first_order_date.dt.to_period('M')
        # Groupby cohort_month: tính mean, median, percentile(90) của total_clv, count cohort_size, trả về DataFrame
    #/Task Execution
    # Input contract: customer_summary phải có customer_unique_id, first_order_date (datetime), total_revenue; order_revenue phải có order_id (PK), payment_value, được aggregate từ order_payments; Join với orders_clean để có customer_unique_id cho mỗi order_id
    # Output contract: DataFrame với cohort_month, cohort_size, mean_clv, median_clv, p90_clv; CLV metrics không null, >= 0; cohort_month sắp xếp tăng dần; Tổng revenue từ output phải khớp với tổng payment_value từ order_revenue (cho delivered orders)
    # Semantic invariants: mean_clv = total_revenue / cohort_size cho từng cohort; p90_clv >= median_clv >= 0 (distribution constraint); CLV tính từ cumulative revenue, không forecast future value
    # Forbidden shortcuts: Không dùng price từ order_items mà phải dùng payment_value từ order_payments; Không tính CLV từ một order mà phải tổng hợp toàn bộ orders của customer; Không bỏ qua orders có nhiều payment methods (aggregate trước khi tính CLV)

def compute_customer_order_distribution(customer_summary: pd.DataFrame) -> pd.DataFrame:
    # Responsibility: Phân bổ khách hàng theo số đơn hàng: tạo bins [1, 2, 3+] từ order_count trong customer_summary, groupby bin để đếm customer_unique_id, tính tỷ lệ phần trăm và cumulative percentage. Trả về bảng distribution summary.
    # Task Execution
        # Validate customer_summary: check order_count >= 1, không null, không duplicate customer_unique_id
        # Tạo order_count_bin = pd.cut([1, 2, 3+]), groupby bin: count customer_unique_id
        # Tính percentage, cumulative_percentage, trả về DataFrame với bins theo thứ tự [1, 2, 3+]
    #/Task Execution
    # Input contract: customer_summary phải có customer_unique_id, order_count (integer, >= 1); Không có customer_unique_id duplicate
    # Output contract: DataFrame với order_count_bin, customer_count, percentage, cumulative_percentage; Tổng customer_count phải bằng số duy nhất customer_unique_id trong input; percentage tổng = 100%, cumulative_percentage kết thúc = 100%
    # Semantic invariants: customer_count >= 0 cho mọi bin; percentage = customer_count / total_customers * 100; cumulative_percentage tăng monotonic
    # Forbidden shortcuts: Không tính order_count từ orders mà phải dùng order_count đã aggregate trong customer_summary; Không dùng customer_id từ orders (mỗi order có customer_id riêng); Không skip validation cho order_count = 0 (invalid state)

def compute_repeat_purchase_time(orders_clean: pd.DataFrame, customer_summary: pd.DataFrame) -> pd.DataFrame:
    # Responsibility: Tính thời gian mua lại trung bình (days between orders) cho khách hàng có order_count >= 2: sort orders_clean theo customer_unique_id và order_purchase_timestamp, tính diff giữa các orders liên tiếp, aggregate mean/median time_to_next_order theo customer_unique_id. Trả về bảng summary với mean, median, p25, p75.
    # Task Execution
        # Filter customer_summary cho order_count >= 2, join với orders_clean on customer_unique_id, sort theo customer_unique_id và order_purchase_timestamp
        # Groupby customer_unique_id: tính diff = timestamp.diff(), drop NaN (first order của mỗi customer), aggregate mean/median diff
        # Tính overall statistics (mean, median, p25, p75) across all customers, trả về DataFrame summary
    #/Task Execution
    # Input contract: orders_clean phải có customer_unique_id, order_purchase_timestamp (datetime, không null), order_id; customer_summary phải có customer_unique_id, order_count >= 2 (filter repeat customers); orders_clean không có duplicate order_id
    # Output contract: DataFrame với customer_unique_id, mean_days_between_orders, median_days_between_orders; Aggregate summary: overall_mean, overall_median, p25, p75 của time_to_next_order; Chỉ bao gồm customers có order_count >= 2
    # Semantic invariants: mean_days_between_orders >= 0; time_to_next_order tính từ order[i+1].timestamp - order[i].timestamp (phải > 0); Chỉ tính cho customers có ít nhất 2 orders
    # Forbidden shortcuts: Không tính từ first_order_date đến last_order_date rồi chia cho order_count (bỏ qua distribution); Không dùng customer_id từ orders thay cho customer_unique_id; Không skip validation cho timestamp null hoặc orders không sắp xếp đúng
```
> **`compute_cohort_retention_matrix`** | **Pipeline:** Phase 3 → Step 3.1 | **Design module:** DM-05 | **Addresses:** FR-01, FR-04 | **Depends on:** *(không có)* | **Called by:** run_multidimensional_analysis
> **`compute_clv_by_cohort`** | **Pipeline:** Phase 3 → Step 3.1 | **Design module:** DM-05 | **Addresses:** FR-01, FR-02, FR-04 | **Depends on:** *(không có)* | **Called by:** run_multidimensional_analysis
> **`compute_customer_order_distribution`** | **Pipeline:** Phase 3 → Step 3.1 | **Design module:** DM-05 | **Addresses:** FR-01, FR-04 | **Depends on:** *(không có)* | **Called by:** run_multidimensional_analysis
> **`compute_repeat_purchase_time`** | **Pipeline:** Phase 3 → Step 3.1 | **Design module:** DM-05 | **Addresses:** FR-01, FR-04 | **Depends on:** *(không có)* | **Called by:** run_multidimensional_analysis


#### File: `analysis/delivery_analysis.py`
```python
def compute_late_rate_by_dimension(orders_clean: pd.DataFrame, order_items: pd.DataFrame, products: pd.DataFrame, customers: pd.DataFrame, sellers: pd.DataFrame, dimension: str, top_n: int = 15) -> pd.DataFrame:
    # Responsibility: Tính tỷ lệ giao trễ theo dimension (customer_state, product_category, seller_id): join orders_clean với customers/order_items/products/sellers, filter order_status='delivered' và đủ cả hai timestamp, groupby dimension để tính late_rate = count(is_late=true) / count(total delivered), avg_late_days, order_count. Trả về top_n dimensions có late_rate cao nhất.
    # Task Execution
        # Filter orders_clean cho order_status='delivered' và không null order_delivered_customer_date, order_estimated_delivery_date; join với customers (customer_state), order_items → products → product_category_name_translation (product_category), sellers (seller_id)
        # Groupby dimension: count is_late=true làm late_count, count total làm delivered_count, mean late_days (chỉ is_late=true)
        # Tính late_rate = late_count / delivered_count, filter order_count >= 10, sort late_rate descending, top_n, trả về DataFrame
    #/Task Execution
    # Input contract: orders_clean phải có is_late (boolean), late_days (float, có thể null), order_status, order_delivered_customer_date, order_estimated_delivery_date; dimension phải trong ['customer_state', 'product_category', 'seller_id']; Chỉ tính trên orders có order_status='delivered' và cả hai timestamp không null
    # Output contract: DataFrame với dimension_value, late_rate (0-1), avg_late_days, order_count; Sắp xếp theo late_rate giảm dần, lấy top_n rows; late_rate = count(is_late) / count(delivered), avg_late_days chỉ tính trên is_late=true
    # Semantic invariants: late_rate trong [0, 1], avg_late_days >= 0; order_count >= min_sample_size (e.g., 10) để tránh statistical noise; Validation report ghi rõ số orders bị loại do thiếu timestamp hoặc chưa delivered
    # Forbidden shortcuts: Không tính late_rate trên tất cả orders mà phải filter delivered với đủ timestamp; Không dùng geolocation_zip_code_prefix cho state-level analysis (dùng customer_state từ customers); Không skip join với product_category_name_translation (category names bằng tiếng Bồ Đào Nha)

def segment_by_late_severity(orders_clean: pd.DataFrame, order_reviews: pd.DataFrame) -> pd.DataFrame:
    # Responsibility: Phân nhóm đơn hàng theo mức độ trễ [on_time, late_1_7, late_8_30, late_30+]: tạo late_severity_bin từ late_days trong orders_clean, join với order_reviews để lấy review_score, groupby late_severity_bin để tính avg_review_score, order_count, tỷ lệ review_score <= 3. Trả về bảng segmentation summary.
    # Task Execution
        # Tạo late_severity_bin = pd.cut(late_days, bins=[-inf, 0, 7, 30, inf], labels=['on_time', 'late_1_7', 'late_8_30', 'late_30+'])
        # Left join orders_clean với order_reviews on order_id, groupby late_severity_bin: count order_id, mean review_score (dropna), count review_score <= 3
        # Tính low_rating_rate = count(review_score <= 3) / count(review_score not null), trả về DataFrame với bins sắp xếp
    #/Task Execution
    # Input contract: orders_clean phải có late_days (float, có thể null cho on_time), order_id, order_status='delivered'; order_reviews phải có order_id, review_score (1-5 integer), có thể null ~43% rows; Join orders_clean với order_reviews on order_id (left join)
    # Output contract: DataFrame với late_severity_bin, order_count, avg_review_score, low_rating_rate (review_score <= 3); Bins theo thứ tự [on_time, late_1_7, late_8_30, late_30+]; avg_review_score chỉ tính trên reviews không null
    # Semantic invariants: late_severity_bin monotonic với late_days (on_time < late_1_7 < late_8_30 < late_30+); avg_review_score trong [1, 5], low_rating_rate trong [0, 1]; order_count tổng phải bằng số delivered orders có đủ timestamp
    # Forbidden shortcuts: Không dùng pd.cut mà không handle negative late_days (early delivery); Không skip null review_score (ghi rõ sample size cho mỗi bin); Không tính avg_review_score trên toàn bộ reviews mà phải group theo late_severity_bin

def compare_repeat_rate_by_first_order_experience(orders_clean: pd.DataFrame, customer_summary: pd.DataFrame) -> pd.DataFrame:
    # Responsibility: So sánh repeat_rate giữa nhóm first-order experience (on_time, late, canceled): join customer_summary với orders_clean (filter first_order_date), gán first_order_experience từ order_status và is_late, groupby first_order_experience để tính repeat_rate = count(order_count >= 2) / count(total customers). Trả về bảng comparison.
    # Task Execution
        # Join customer_summary với orders_clean on customer_unique_id, filter order_purchase_timestamp = first_order_date để lấy first order; tạo first_order_experience = case when order_status='canceled' then 'canceled' when is_late=true then 'late' else 'on_time'
        # Groupby first_order_experience: count customer_unique_id làm customer_count, count repeat_purchase=true làm repeat_customer_count
        # Tính repeat_rate = repeat_customer_count / customer_count, trả về DataFrame với comparison table
    #/Task Execution
    # Input contract: customer_summary phải có customer_unique_id, first_order_date, order_count, repeat_purchase (boolean); orders_clean phải có customer_unique_id, order_purchase_timestamp, order_status, is_late; Join customer_summary với orders_clean on (customer_unique_id, first_order_date=order_purchase_timestamp) để lấy first order
    # Output contract: DataFrame với first_order_experience, customer_count, repeat_customer_count, repeat_rate; first_order_experience trong ['on_time', 'late', 'canceled']; repeat_rate = repeat_customer_count / customer_count, trong [0, 1]
    # Semantic invariants: repeat_rate(on_time) >= repeat_rate(late) >= repeat_rate(canceled) (hypothesis to test); Tổng customer_count phải bằng tổng customer_unique_id duy nhất; repeat_customer_count = count(order_count >= 2)
    # Forbidden shortcuts: Không dùng customer_id từ orders mà phải dùng customer_unique_id; Không tính repeat_rate từ tất cả orders mà phải filter first order experience; Không skip validation cho customers không có first_order mapping
```
> **`compute_late_rate_by_dimension`** | **Pipeline:** Phase 3 → Step 3.2 | **Design module:** DM-05 | **Addresses:** FR-03, FR-04, FR-05 | **Depends on:** *(không có)* | **Called by:** run_multidimensional_analysis
> **`segment_by_late_severity`** | **Pipeline:** Phase 3 → Step 3.2 | **Design module:** DM-05 | **Addresses:** FR-03, FR-04 | **Depends on:** *(không có)* | **Called by:** run_multidimensional_analysis
> **`compare_repeat_rate_by_first_order_experience`** | **Pipeline:** Phase 3 → Step 3.2 | **Design module:** DM-05 | **Addresses:** FR-01, FR-03, FR-04 | **Depends on:** *(không có)* | **Called by:** run_multidimensional_analysis


#### File: `analysis/revenue_analysis.py`
```python
def compute_revenue_trend_by_month(order_revenue: pd.DataFrame, orders_clean: pd.DataFrame) -> pd.DataFrame:
    # Responsibility: Phân tích xu hướng doanh thu theo tháng: join order_revenue với orders_clean on order_id, extract month từ order_purchase_timestamp, groupby month để tính total_revenue (sum payment_value), order_count, AOV (avg), freight_ratio (freight_value / payment_value), MoM_growth (%). Trả về bảng revenue_trend.
    # Task Execution
        # Join order_revenue với orders_clean on order_id, filter order_status='delivered', extract month = order_purchase_timestamp.dt.to_period('M')
        # Groupby month: sum payment_value làm total_revenue, sum freight_value, count order_id, mean payment_value làm aov
        # Tính freight_ratio, mom_growth_pct = (total_revenue - total_revenue.shift(1)) / total_revenue.shift(1) * 100, trả về DataFrame
    #/Task Execution
    # Input contract: order_revenue phải có order_id (PK), payment_value, product_value, freight_value (aggregate từ order_payments); orders_clean phải có order_id, order_purchase_timestamp (datetime), order_status='delivered'; Tổng payment_value từ order_revenue phải khớp với tổng order_payments gốc
    # Output contract: DataFrame với month, total_revenue, order_count, aov, freight_ratio, mom_growth_pct; month sắp xếp tăng dần (datetime period 'M'); freight_ratio = total_freight_value / total_payment_value, trong [0, 1]
    # Semantic invariants: aov = total_revenue / order_count; mom_growth_pct = (revenue[t] - revenue[t-1]) / revenue[t-1] * 100; freight_ratio >= 0, thường trong [0.05, 0.30] (freight 5-30% của total)
    # Forbidden shortcuts: Không dùng price từ order_items mà phải dùng payment_value từ order_payments; Không tính revenue từ tất cả orders mà phải filter delivered; Không skip aggregate order_payments theo order_id trước (một order có nhiều payment methods)

def compute_revenue_by_dimension(order_revenue: pd.DataFrame, orders_clean: pd.DataFrame, order_items: pd.DataFrame, products: pd.DataFrame, customers: pd.DataFrame, dimension: str, top_n: int = 15) -> pd.DataFrame:
    # Responsibility: Phân rã doanh thu theo dimension (product_category, customer_state, payment_type): join order_revenue với orders_clean, order_items, products, customers, groupby dimension để tính total_revenue, order_count, aov, freight_ratio. Trả về top_n dimensions có total_revenue cao nhất.
    # Task Execution
        # Join order_revenue với orders_clean on order_id, filter order_status='delivered'; join với order_items → products → product_category_name_translation (category), customers (state), hoặc lấy payment_type từ order_revenue
        # Groupby dimension: sum payment_value làm total_revenue, sum freight_value, count order_id, mean payment_value làm aov
        # Tính freight_ratio, sort total_revenue descending, top_n, trả về DataFrame
    #/Task Execution
    # Input contract: dimension phải trong ['product_category', 'customer_state', 'payment_type']; order_revenue phải có order_id, payment_value, freight_value, payment_type; Join với orders_clean → order_items → products → product_category_name_translation (cho category), customers (cho state)
    # Output contract: DataFrame với dimension_value, total_revenue, order_count, aov, freight_ratio; Sắp xếp theo total_revenue giảm dần, lấy top_n rows; freight_ratio = sum(freight_value) / sum(payment_value)
    # Semantic invariants: Tổng total_revenue từ output phải <= tổng payment_value từ order_revenue (delivered orders); aov = total_revenue / order_count; freight_ratio >= 0
    # Forbidden shortcuts: Không dùng geolocation_zip_code_prefix cho state-level analysis (dùng customer_state); Không skip join với product_category_name_translation (category names tiếng Bồ Đào Nha); Không aggregate order_items.price thay vì payment_value từ order_payments

def compute_controlled_correlation_matrix(orders_clean: pd.DataFrame, order_revenue: pd.DataFrame, order_reviews: pd.DataFrame, customer_summary: pd.DataFrame, control_vars: list) -> pd.DataFrame:
    # Responsibility: Tính ma trận tương quan có kiểm soát (partial correlation) giữa late_days, review_score, order_revenue, repeat_purchase với biến kiểm soát (tháng mua, danh mục, bang): merge tất cả input tables, standardize continuous vars, fit OLS regression với control variables, tính partial correlation từ residuals. Trả về correlation matrix với p-values.
    # Task Execution
        # Merge orders_clean với order_revenue, order_reviews, customer_summary; filter order_status='delivered', dropna cho [late_days, review_score, payment_value]; standardize continuous vars (mean=0, std=1)
        # One-hot encode control_vars (month, product_category, customer_state); fit OLS regression cho từng target variable [late_days, review_score, order_revenue, repeat_purchase] với control_vars làm predictors, lấy residuals
        # Tính pearson correlation giữa các residuals pairs, compute p-values từ scipy.stats, trả về correlation matrix với p-values và sample size
    #/Task Execution
    # Input contract: orders_clean phải có order_id, late_days, customer_unique_id, order_purchase_timestamp, customer_state, product_category; order_revenue phải có order_id, payment_value; order_reviews phải có order_id, review_score (có thể null)
    # Output contract: DataFrame correlation matrix (4x4) với variables [late_days, review_score, order_revenue, repeat_purchase]; Correlation coefficients trong [-1, 1], p-values trong [0, 1]; Ghi rõ sample size sau dropna và degrees of freedom
    # Semantic invariants: Partial correlation tính từ residuals sau khi regress out control variables; correlation(X, Y | Z) != correlation(X, Y) (controlled correlation khác simple correlation); p-value < 0.05 → significant correlation (α=0.05)
    # Forbidden shortcuts: Không tính simple pearson correlation mà bỏ qua control variables; Không standardize continuous vars trước regression (scale khác nhau); Không ghi rõ sample size và significance threshold (misleading interpretation)
```
> **`compute_revenue_trend_by_month`** | **Pipeline:** Phase 3 → Step 3.3 | **Design module:** DM-05 | **Addresses:** FR-02, FR-04, FR-06 | **Depends on:** *(không có)* | **Called by:** run_multidimensional_analysis
> **`compute_revenue_by_dimension`** | **Pipeline:** Phase 3 → Step 3.3 | **Design module:** DM-05 | **Addresses:** FR-02, FR-04, FR-05 | **Depends on:** *(không có)* | **Called by:** run_multidimensional_analysis
> **`compute_controlled_correlation_matrix`** | **Pipeline:** Phase 3 → Step 3.3 | **Design module:** DM-05 | **Addresses:** FR-04, FR-06 | **Depends on:** *(không có)* | **Called by:** run_multidimensional_analysis


#### File: `analysis/__init__.py`
```python
def run_multidimensional_analysis(customer_summary: pd.DataFrame, orders_clean: pd.DataFrame, order_revenue: pd.DataFrame, order_items: pd.DataFrame, products: pd.DataFrame, customers: pd.DataFrame, sellers: pd.DataFrame, order_reviews: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    # Responsibility: 
```
> **`run_multidimensional_analysis`** | **Pipeline:** Phase 3 → Step | **Design module:** DM-05 | **Addresses:** N/A | **Depends on:** *(không có)* | **Called by:** *(không có)*


### Folder: `validation/`

#### File: `validation/metrics_validator.py`
```python
def validate_customer_unique_id_count(customer_summary: pd.DataFrame, customers_raw: pd.DataFrame, orders_raw: pd.DataFrame) -> Dict[str, Any]:
    # Responsibility: Xác nhận tổng số customer_unique_id trong customer_summary khớp với số customer_unique_id duy nhất từ bảng customers gốc sau khi nối với orders. Trả về expected count, actual count, delta và validation status.
    # Task Execution
        # Nối customers_raw với orders_raw qua customer_unique_id và customer_id, lấy danh sách customer_unique_id duy nhất từ kết quả nối
        # Đếm số customer_unique_id duy nhất từ customer_summary (actual_count)
        # So sánh expected_count với actual_count, tính delta và trả về validation report với is_valid flag
    #/Task Execution
    # Input contract: customer_summary có cột customer_unique_id làm khóa chính; customers_raw và orders_raw từ DM-01 chưa được transform; orders_raw có cột customer_id để nối với customers_raw.customer_unique_id
    # Output contract: Dict gồm expected_count (int), actual_count (int), delta (int), is_valid (bool); is_valid=True khi delta=0; Ghi rõ lý do nếu is_valid=False
    # Semantic invariants: Không đếm customer_id từ orders_raw trực tiếp mà phải đếm customer_unique_id từ customers sau khi nối; expected_count phải bằng số dòng trong customer_summary vì customer_unique_id là khóa chính
    # Forbidden shortcuts: Không dùng orders.customer_id để đếm khách hàng vì một khách có nhiều customer_id; Không bỏ qua validation khi số lượng 'gần đúng'; Không aggregate trước khi nối customers với orders

def validate_revenue_totals(order_revenue: pd.DataFrame, order_payments_raw: pd.DataFrame, orders_clean: pd.DataFrame) -> Dict[str, Any]:
    # Responsibility: Xác nhận tổng payment_value trong order_revenue bằng tổng payment_value từ order_payments gốc cho tập đơn đã giao (order_status='delivered'). Trả về expected revenue, actual revenue, delta tuyệt đối và phần trăm.
    # Task Execution
        # Filter orders_clean lấy tập order_id có order_status='delivered', nối với order_payments_raw và tính tổng payment_value (expected_revenue)
        # Tính tổng total_payment_value từ order_revenue cho cùng tập order_id delivered (actual_revenue)
        # Tính delta tuyệt đối và phần trăm, trả về validation report với is_valid flag và số đơn delivered
    #/Task Execution
    # Input contract: order_revenue có cột order_id và total_payment_value; order_payments_raw có cột order_id và payment_value; orders_clean có cột order_id và order_status để filter delivered
    # Output contract: Dict gồm expected_revenue (float), actual_revenue (float), delta_abs (float), delta_pct (float), is_valid (bool); is_valid=True khi delta_abs < 0.01 BRL (tolerance cho floating point); Ghi rõ số đơn delivered được dùng để validation
    # Semantic invariants: Chỉ tính revenue cho đơn có order_status='delivered'; order_revenue.total_payment_value phải aggregate từ order_payments theo order_id trước khi nối với orders
    # Forbidden shortcuts: Không dùng price × quantity từ order_items thay vì payment_value từ order_payments; Không bỏ qua filter order_status='delivered'; Không chấp nhận delta > 1% mà không ghi log chi tiết

def validate_late_delivery_rate(orders_clean: pd.DataFrame) -> Dict[str, Any]:
    # Responsibility: Xác nhận tỷ lệ giao trễ chỉ được tính trên đơn delivered có đủ cả hai timestamp (order_delivered_customer_date và order_estimated_delivery_date). Trả về số đơn delivered có đủ timestamp, số đơn trễ, tỷ lệ trễ, số đơn bị loại và lý do.
    # Task Execution
        # Filter orders_clean lấy đơn order_status='delivered' có cả hai timestamp not null, đếm số đơn (total_delivered_with_timestamps)
        # Đếm số đơn is_late=True trong tập đơn đã filter (late_count), tính late_rate = late_count / total
        # Tính exclusion_reasons: đếm đơn không delivered, đơn thiếu delivered_date, đơn thiếu estimated_date, trả về validation report
    #/Task Execution
    # Input contract: orders_clean có cột is_late (boolean), order_status, order_delivered_customer_date, order_estimated_delivery_date; is_late được tính từ order_delivered_customer_date > order_estimated_delivery_date
    # Output contract: Dict gồm total_delivered_with_timestamps (int), late_count (int), late_rate (float), excluded_count (int), exclusion_reasons (dict); late_rate = late_count / total_delivered_with_timestamps; exclusion_reasons liệt kê: số đơn chưa giao, số đơn thiếu delivered_date, số đơn thiếu estimated_date
    # Semantic invariants: Chỉ tính late_rate trên tập đơn order_status='delivered' có cả hai timestamp not null; is_late=True chỉ khi order_delivered_customer_date > order_estimated_delivery_date
    # Forbidden shortcuts: Không tính late_rate trên toàn bộ orders mà không filter delivered; Không bỏ qua kiểm tra null timestamp; Không dùng approximation hoặc imputation cho missing timestamp
```
> **`validate_customer_unique_id_count`** | **Pipeline:** Phase 4 → Step 4.1 | **Design module:** DM-06 | **Addresses:** FR-01 | **Depends on:** *(không có)* | **Called by:** run_validation
> **`validate_revenue_totals`** | **Pipeline:** Phase 4 → Step 4.1 | **Design module:** DM-06 | **Addresses:** FR-02 | **Depends on:** *(không có)* | **Called by:** run_validation
> **`validate_late_delivery_rate`** | **Pipeline:** Phase 4 → Step 4.1 | **Design module:** DM-06 | **Addresses:** FR-03 | **Depends on:** *(không có)* | **Called by:** run_validation


#### File: `validation/baseline_comparator.py`
```python
def compare_cohort_retention_vs_baseline(cohort_retention: pd.DataFrame, baseline_repeat_rate: float) -> Dict[str, Any]:
    # Responsibility: So sánh cohort retention (retention_m1, retention_m3, retention_m6 theo cohort_month) với baseline repeat_rate tổng thể. Tính chênh lệch tỷ lệ giữa cohort tốt nhất và xấu nhất, thực hiện proportions_ztest và trả về p-value, effect size.
    # Task Execution
        # Tìm cohort có retention_m3 cao nhất và thấp nhất (filter cohort có customer_count >= 30), tính delta_retention
        # Thực hiện proportions_ztest giữa hai cohort (dùng retention_m3 × customer_count làm success count), lấy p_value
        # Tính effect_size = delta / pooled_std, so sánh với baseline_repeat_rate và trả về comparison report
    #/Task Execution
    # Input contract: cohort_retention có cột cohort_month, retention_m1, retention_m3, retention_m6, customer_count; baseline_repeat_rate là float từ 0 đến 1 (tỷ lệ mua lặp lại tổng thể); retention_m1/m3/m6 là tỷ lệ từ 0 đến 1
    # Output contract: Dict gồm best_cohort (str), worst_cohort (str), delta_retention (float), p_value (float), effect_size (float), is_significant (bool); is_significant=True khi p_value < 0.05; effect_size = (best_retention - worst_retention) / pooled_std
    # Semantic invariants: Chỉ so sánh retention_rate giữa các cohort có customer_count >= 30 để đảm bảo statistical power; p_value được tính từ proportions_ztest giữa cohort tốt nhất và xấu nhất
    # Forbidden shortcuts: Không so sánh trung bình retention mà phải dùng proportions test; Không bỏ qua baseline_repeat_rate khi đánh giá giá trị gia tăng của cohort analysis; Không chấp nhận chênh lệch < 5% mà không kiểm tra statistical significance

def compare_risk_segmentation_vs_baseline(risk_segmentation: pd.DataFrame, baseline_late_rate: float) -> Dict[str, Any]:
    # Responsibility: So sánh risk segmentation (repeat_rate theo nhóm rủi ro: late × review_score × order_value) với baseline repeat_rate. Tính chênh lệch repeat_rate giữa nhóm rủi ro cao và thấp, thực hiện proportions_ztest và trả về p-value.
    # Task Execution
        # Tìm risk_group có repeat_rate thấp nhất (high_risk) và cao nhất (low_risk), filter nhóm có customer_count >= 30
        # Thực hiện proportions_ztest giữa hai nhóm (dùng repeat_rate × customer_count làm success count), lấy p_value
        # Kiểm tra logic: high_risk phải có repeat_rate thấp hơn low_risk, so sánh với baseline_late_rate và trả về comparison report
    #/Task Execution
    # Input contract: risk_segmentation có cột risk_group, repeat_rate, customer_count; baseline_late_rate là tỷ lệ giao trễ tổng thể (float từ 0 đến 1); risk_group được phân loại theo tổ hợp is_late × review_score × order_value
    # Output contract: Dict gồm high_risk_group (str), low_risk_group (str), delta_repeat_rate (float), p_value (float), is_significant (bool); is_significant=True khi p_value < 0.05; Ghi rõ nhóm nào có repeat_rate cao/thấp nhất
    # Semantic invariants: Nhóm rủi ro cao phải có repeat_rate thấp hơn nhóm rủi ro thấp để xác nhận logic segmentation; Chỉ so sánh nhóm có customer_count >= 30
    # Forbidden shortcuts: Không dùng t-test cho tỷ lệ mà phải dùng proportions_ztest; Không bỏ qua baseline_late_rate khi đánh giá tác động của giao trễ lên repeat_rate; Không chấp nhận kết quả nếu high_risk_group có repeat_rate cao hơn low_risk_group

def compare_revenue_decomposition_vs_baseline(revenue_decomposition: pd.DataFrame, baseline_monthly_revenue: pd.DataFrame) -> Dict[str, Any]:
    # Responsibility: So sánh revenue decomposition (doanh thu theo category/state/payment_method) với baseline monthly revenue tổng thể. Xác định top category/state có doanh thu cao nhất, tính contribution %, thực hiện t-test so sánh trung bình revenue giữa nhóm.
    # Task Execution
        # Tính tổng revenue từ revenue_decomposition, so sánh với tổng baseline_monthly_revenue để xác nhận consistency
        # Tìm top dimension có revenue cao nhất, tính contribution_pct = top_revenue / total_revenue
        # Thực hiện t-test so sánh mean revenue giữa top dimension và các dimension khác (hoặc ANOVA nếu có nhiều nhóm), trả về comparison report với p_value và contribution_pct
    #/Task Execution
    # Input contract: revenue_decomposition có cột dimension (category/state/payment_method), revenue (BRL), order_count; baseline_monthly_revenue có cột order_month, total_revenue; revenue_decomposition đã aggregate theo dimension
    # Output contract: Dict gồm top_dimension (str), top_revenue (float), contribution_pct (float), p_value (float), is_significant (bool); contribution_pct = top_revenue / total_revenue từ baseline; is_significant=True khi top dimension có contribution >= 20% hoặc p_value < 0.05 khi so sánh với các dimension khác
    # Semantic invariants: Tổng revenue từ revenue_decomposition phải bằng tổng revenue từ baseline_monthly_revenue; Top dimension phải có contribution_pct >= 10% để xác nhận giá trị phân tích
    # Forbidden shortcuts: Không dùng chi-square test cho continuous revenue mà phải dùng t-test hoặc ANOVA; Không bỏ qua kiểm tra tổng revenue khớp giữa decomposition và baseline; Không chấp nhận top dimension có contribution < 10% mà không ghi cảnh báo
```
> **`compare_cohort_retention_vs_baseline`** | **Pipeline:** Phase 4 → Step 4.2 | **Design module:** DM-06 | **Addresses:** FR-06 | **Depends on:** *(không có)* | **Called by:** run_validation
> **`compare_risk_segmentation_vs_baseline`** | **Pipeline:** Phase 4 → Step 4.2 | **Design module:** DM-06 | **Addresses:** FR-06 | **Depends on:** *(không có)* | **Called by:** run_validation
> **`compare_revenue_decomposition_vs_baseline`** | **Pipeline:** Phase 4 → Step 4.2 | **Design module:** DM-06 | **Addresses:** FR-06 | **Depends on:** *(không có)* | **Called by:** run_validation


#### File: `validation/traceability_checker.py`
```python
def build_traceability_matrix(recommendations: List[Dict], insights: List[Dict]) -> pd.DataFrame:
    # Responsibility: Xây dựng traceability matrix mapping recommendation_id → insight_id → evidence_summary. Xác minh mỗi khuyến nghị có gắn với ít nhất một insight, mỗi insight có bằng chứng định lượng (số tuyệt đối, tỷ lệ %, xu hướng thời gian hoặc so sánh nhóm).
    # Task Execution
        # Iterate qua recommendations, lấy insight_ids từ mỗi recommendation và nối với insights để lấy evidence_type và quantitative_value
        # Với mỗi cặp (recommendation_id, insight_id), tạo evidence_summary từ quantitative_value, đánh dấu has_quantitative_evidence=True nếu evidence_type hợp lệ và quantitative_value not null
        # Trả về DataFrame traceability matrix, ghi log warning cho recommendation không có insight_ids hoặc insight thiếu quantitative evidence
    #/Task Execution
    # Input contract: recommendations là list dict có key: recommendation_id, description, insight_ids (list), impact_score, difficulty_score, risk_score; insights là list dict có key: insight_id, description, evidence_type (numeric/trend/comparison), quantitative_value (str hoặc number); insight_ids trong recommendations phải tham chiếu đến insight_id trong insights
    # Output contract: DataFrame có cột recommendation_id, insight_id, evidence_summary, has_quantitative_evidence (bool); has_quantitative_evidence=True khi insight có quantitative_value not null và evidence_type hợp lệ; Mỗi recommendation_id xuất hiện ít nhất một lần trong matrix
    # Semantic invariants: Mỗi recommendation_id phải có ít nhất một insight_id hợp lệ; Mỗi insight_id được tham chiếu phải có quantitative_value cụ thể (không phải 'có xu hướng tăng' mà phải 'tăng 15% từ tháng 1 đến tháng 6')
    # Forbidden shortcuts: Không chấp nhận insight có evidence_type='qualitative' hoặc quantitative_value null; Không tạo mapping giả định khi insight_ids không tồn tại trong insights; Không bỏ qua validation khi recommendation không có insight_ids

def classify_recommendations(traceability_matrix: pd.DataFrame, recommendations: List[Dict]) -> Dict[str, List[Dict]]:
    # Responsibility: Phân loại khuyến nghị thành hai nhóm: (1) qualified (có đầy đủ bằng chứng + phân loại impact × difficulty × risk), (2) rejected (thiếu bằng chứng hoặc dựa trên giả định không kiểm chứng). Chỉ giữ 3-5 khuyến nghị ưu tiên cao nhất trong qualified.
    # Task Execution
        # Group traceability_matrix theo recommendation_id, đếm số insight có has_quantitative_evidence=True cho mỗi recommendation
        # Filter recommendations: qualified = có ít nhất 1 quantitative evidence và priority_tier in ['high', 'medium'], rejected = không có evidence hoặc priority_tier='low'
        # Sort qualified theo priority_tier desc, impact_score desc, lấy top 3-5 khuyến nghị, trả về dict {qualified, rejected}
    #/Task Execution
    # Input contract: traceability_matrix có cột recommendation_id, has_quantitative_evidence; recommendations là list dict có key: recommendation_id, description, impact_score, difficulty_score, risk_score, priority_tier; priority_tier đã được tính từ impact × difficulty × risk
    # Output contract: Dict gồm qualified (list dict), rejected (list dict); qualified chứa tối đa 5 khuyến nghị có priority_tier='high' và has_quantitative_evidence=True; rejected chứa khuyến nghị không có quantitative evidence hoặc priority_tier='low'
    # Semantic invariants: Mỗi khuyến nghị trong qualified phải có ít nhất một insight với has_quantitative_evidence=True; Qualified được xếp theo priority_tier (high > medium > low) và impact_score (cao > thấp)
    # Forbidden shortcuts: Không đưa khuyến nghị vào qualified nếu không có quantitative evidence; Không giữ > 5 khuyến nghị trong qualified mà không có lý do rõ ràng; Không bỏ qua kiểm tra priority_tier khi xếp hạng
```
> **`build_traceability_matrix`** | **Pipeline:** Phase 4 → Step 4.3 | **Design module:** DM-06 | **Addresses:** FR-08 | **Depends on:** *(không có)* | **Called by:** run_validation
> **`classify_recommendations`** | **Pipeline:** Phase 4 → Step 4.3 | **Design module:** DM-06 | **Addresses:** FR-08, FR-09 | **Depends on:** build_traceability_matrix | **Called by:** run_validation


#### File: `validation/__init__.py`
```python
def run_validation(customer_summary: pd.DataFrame, order_revenue: pd.DataFrame, orders_clean: pd.DataFrame, customers_raw: pd.DataFrame, order_payments_raw: pd.DataFrame, cohort_retention: pd.DataFrame, risk_segmentation: pd.DataFrame, revenue_decomposition: pd.DataFrame, baseline_metrics: Dict, recommendations: List[Dict], insights: List[Dict]) -> Dict[str, Any]:
    # Responsibility: Tổng hợp tất cả validation checks từ step 4.1, 4.2, 4.3: (1) Validate chỉ số nền (customer, revenue, late_rate), (2) So sánh insight với baseline, (3) Kiểm tra traceability khuyến nghị. Trả về validation report tổng hợp cho báo cáo cuối (AT-005).
    # Task Execution
        # Gọi validate_customer_unique_id_count, validate_revenue_totals, validate_late_delivery_rate từ metrics_validator.py, aggregate kết quả vào metrics_validation dict
        # Gọi compare_cohort_retention_vs_baseline, compare_risk_segmentation_vs_baseline, compare_revenue_decomposition_vs_baseline từ baseline_comparator.py, aggregate kết quả vào baseline_comparison dict
        # Gọi build_traceability_matrix và classify_recommendations từ traceability_checker.py, aggregate kết quả vào traceability dict, tính overall_status từ tất cả is_valid/is_significant flags, trả về validation report tổng hợp
    #/Task Execution
    # Input contract: customer_summary, order_revenue, orders_clean từ DM-03; customers_raw, order_payments_raw từ DM-01; cohort_retention, risk_segmentation, revenue_decomposition từ DM-05
    # Output contract: Dict gồm: metrics_validation (dict từ step 4.1), baseline_comparison (dict từ step 4.2), traceability (dict từ step 4.3), overall_status (str: pass/warning/fail); overall_status='pass' khi tất cả validation checks đạt, 'warning' khi có minor issues, 'fail' khi có critical issues; Mỗi phần validation có is_valid hoặc is_significant flag
    # Semantic invariants: overall_status='fail' nếu bất kỳ metrics_validation nào có is_valid=False; overall_status='warning' nếu baseline_comparison không có insight nào is_significant=True
    # Forbidden shortcuts: Không bỏ qua bất kỳ validation function nào từ step 4.1, 4.2, 4.3; Không trả về overall_status='pass' khi có critical validation failure; Không aggregate validation report mà không ghi rõ từng phần (metrics, baseline, traceability)
```
> **`run_validation`** | **Pipeline:** Phase 4 → Step 4.1, 4.2, 4.3 | **Design module:** DM-06 | **Addresses:** FR-01, FR-02, FR-03, FR-06, FR-08, FR-09, FR-10 | **Depends on:** validate_customer_unique_id_count, validate_revenue_totals, validate_late_delivery_rate, compare_cohort_retention_vs_baseline, compare_risk_segmentation_vs_baseline, compare_revenue_decomposition_vs_baseline, build_traceability_matrix, classify_recommendations | **Called by:** *(không có)*

