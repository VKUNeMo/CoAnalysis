# Báo cáo Phân tích Dữ liệu Olist Brazilian E-Commerce

Báo cáo này trình bày các phân tích chuyên sâu về **tỷ lệ giữ chân khách hàng (retention)**, **hiệu suất giao hàng và sự chậm trễ (delivery performance)**, cùng với **xu hướng doanh thu (revenue trends)** từ bộ dữ liệu Olist (Brazil) giai đoạn 2016 - 2018.

---

## 1. Tóm tắt Chỉ số Cốt lõi (Executive Summary)

Dưới đây là các chỉ số tổng quan được trích xuất từ bộ dữ liệu:

*   **Tổng doanh thu (chưa gồm phí ship):** 13,494,400.74 BRL
*   **Tổng chi phí vận chuyển (freight):** 2,241,126.29 BRL (chiếm **14.24%** tổng chi tiêu)
*   **Tổng số khách hàng độc nhất:** 94,990 khách hàng
*   **Số lượng khách hàng quay lại mua hàng:** 2,888 khách hàng
*   **Tỷ lệ mua lại (Repeat Purchase Rate):** **3.04%**
*   **Thời gian giao hàng thực tế trung bình:** **12.56 ngày**
*   **Thời gian giao hàng ước tính trung bình:** **23.74 ngày**
*   **Tỷ lệ đơn hàng bị trễ hạn:** **8.11%**
*   **Điểm đánh giá trung bình (Review Score):** **4.09 / 5.0**

---

## 2. Phân tích Chi tiết các Yếu tố

### 2.1. Tỷ lệ Giữ chân Khách hàng (Customer Retention & Cohort)

Một trong những phát hiện đáng chú ý nhất từ bộ dữ liệu Olist là **Tỷ lệ giữ chân khách hàng cực kỳ thấp**. 

*   **Tỷ lệ quay lại mua hàng (Repeat Purchase Rate) chỉ đạt 3.04%**. Nghĩa là trong gần 95,000 khách hàng độc nhất, có tới 96.96% khách hàng chỉ thực hiện duy nhất 1 giao dịch trên nền tảng trong suốt gần 3 năm.
*   **Phân tích Cohort năm 2017:** Biểu đồ Cohort bên dưới theo dõi hành vi của các khách hàng bắt đầu mua hàng từ tháng 1/2017 đến tháng 12/2017. Qua các tháng tiếp theo (Month 1, Month 2,...), tỷ lệ khách hàng hoạt động trở lại hầu như đều **dưới 1%** (thường dao động từ 0.2% đến 0.7%).

![Biểu đồ Cohort Retention 2017](plots/cohort_retention_2017.png)

#### Nguyên nhân dẫn đến tỷ lệ giữ chân thấp:
1.  **Mô hình Marketplace thuần túy:** Olist hoạt động như một bên trung gian kết nối các cửa hàng nhỏ (sellers) với các sàn thương mại điện tử lớn. Khách hàng thường không nhận thức được họ đang mua hàng qua Olist mà nghĩ rằng họ mua trực tiếp từ các nhà bán lẻ khác, dẫn đến lòng trung thành với thương hiệu Olist rất kém.
2.  **Chi phí vận chuyển cao và thời gian giao hàng lâu:** Phí vận chuyển chiếm trung bình tới 14.24% giá trị đơn hàng, kết hợp với thời gian giao hàng trung bình lên đến hơn 12 ngày làm giảm đáng kể động lực mua sắm lặp lại của khách hàng.

---

### 2.2. Thời gian Giao hàng và Sự chậm trễ (Delivery Delays)

Hiệu suất giao hàng là yếu tố sống còn đối với sự hài lòng của khách hàng trong ngành thương mại điện tử. 

*   **Under-promise & Over-deliver:** Olist đưa ra thời gian giao hàng ước tính rất an toàn (trung bình **23.74 ngày**), trong khi thời gian thực tế trung bình để khách nhận được hàng là **12.56 ngày**. Việc này giúp đa số khách hàng nhận được hàng sớm hơn dự kiến.
*   **Tỷ lệ giao hàng trễ hạn:** Có **8.11%** tổng số đơn hàng giao thành công bị trễ so với thời hạn ước tính ban đầu. Đối với những đơn hàng bị trễ này, thời gian trễ trung bình là **9.55 ngày**.

#### Tác động của sự chậm trễ đến mức độ hài lòng (Review Score):
Có sự tương quan nghịch rõ rệt (hệ số tương quan **-0.27**) giữa số ngày trễ hạn và điểm đánh giá. 
Khi đơn hàng được giao đúng hạn hoặc sớm hơn, điểm đánh giá trung bình đạt **4.29 / 5.0**. Tuy nhiên, chỉ cần trễ từ 1-7 ngày, điểm đánh giá lập tức giảm mạnh xuống **3.18 / 5.0**. Nếu trễ trên 8 ngày, điểm số rơi thảm hại xuống dưới **1.75 / 5.0**.

![Mức độ hài lòng theo thời gian giao hàng](plots/review_score_by_delay.png)

#### Sự khác biệt về địa lý (Geography):
Brazil là một quốc gia có diện tích rộng lớn với hạ tầng giao thông không đồng đều. Hầu hết các nhà bán hàng (sellers) tập trung ở khu vực miền Nam và Đông Nam (đặc biệt là bang São Paulo - SP).
*   **Các bang có tỷ lệ trễ hạn cao nhất:** AL (Alagoas - **23.9%**), MA (Maranhão - **19.7%**), PI (Piauí - **16.0%**), CE (Ceará - **15.3%**). Các bang này nằm ở vùng Đông Bắc, có khoảng cách xa và hạ tầng logistics kém phát triển. Thời gian giao hàng thực tế tại đây lên tới 20 - 24 ngày.
*   **Các bang có tỷ lệ trễ hạn thấp nhất:** SP (São Paulo - **5.89%** trễ, giao hàng nhanh nhất chỉ với **8.76 ngày** nhờ lợi thế tập trung người bán), PR (Paraná - **5.00%**), MG (Minas Gerais - **5.61%**).

![Tỷ lệ trễ hạn theo bang](plots/delay_rate_by_state.png)

#### Sự chậm trễ theo danh mục sản phẩm:
Các mặt hàng cồng kềnh, nặng hoặc có quy trình đóng gói phức tạp thường có tỷ lệ trễ cao hơn. Ví dụ, danh mục *Office Furniture* và *Housewares* nằm trong số các ngành hàng có tỷ lệ trễ đơn cao nhất trong top 15 ngành hàng phổ biến.

![Tỷ lệ trễ hạn theo danh mục](plots/delay_rate_by_category.png)

---

### 2.3. Xu hướng Doanh thu (Revenue Trends)

#### Tăng trưởng theo thời gian:
Doanh thu của Olist chứng kiến sự tăng trưởng vượt bậc trong năm 2017 và duy trì mức ổn định cao trong năm 2018. 
*   **Đỉnh điểm doanh thu:** Đạt kỷ lục vào **tháng 11/2017** với **1,003,862.14 BRL** doanh thu từ **7,421 đơn hàng**, tăng trưởng **52%** so với tháng trước đó. Đây là kết quả trực tiếp từ chiến dịch **Black Friday**.
*   **Xu hướng 2018:** Doanh thu duy trì ổn định ở mức cao từ **850,000 BRL đến 990,000 BRL** mỗi tháng, cho thấy nền tảng đã bước vào giai đoạn trưởng thành và định hình được thị phần ổn định.

![Xu hướng doanh thu và đơn hàng theo tháng](plots/monthly_revenue_orders.png)

#### Danh mục sản phẩm đóng góp doanh thu lớn nhất:
Top 5 ngành hàng mang lại doanh thu cao nhất cho Olist gồm:
1.  **Health Beauty (Sức khỏe & Làm đẹp):** 1,255,695.13 BRL
2.  **Watches Gifts (Đồng hồ & Quà tặng):** 1,198,185.21 BRL
3.  **Bed Bath Table (Chăn ga gối đệm):** 1,035,964.06 BRL
4.  **Sports Leisure (Thể thao & Giải trí):** 979,740.92 BRL
5.  **Computers Accessories (Máy tính & Phụ kiện):** 904,322.02 BRL

![Top danh mục theo doanh thu](plots/top_categories_revenue.png)

#### Phân bố doanh thu theo bang:
Tập trung cực kỳ cao tại khu vực Đông Nam Brazil:
*   **SP (São Paulo):** Chiếm vị trí độc tôn với **5,163,867.22 BRL** (khoảng **38.3%** tổng doanh thu toàn quốc).
*   **RJ (Rio de Janeiro):** Xếp thứ hai với **1,811,623.42 BRL** (~13.4%).
*   **MG (Minas Gerais):** Xếp thứ ba với **1,573,508.20 BRL** (~11.7%).
*   Ba bang hàng đầu này đã chiếm tới **hơn 63%** tổng doanh thu của Olist.

![Top bang đóng góp doanh thu](plots/top_states_revenue.png)

#### Phương thức thanh toán:
*   **Thẻ tín dụng (Credit Card):** Là phương thức thanh toán áp đảo nhất, chiếm **78.4%** tổng giá trị giao dịch. Điều này là do người tiêu dùng Brazil rất ưa chuộng hình thức mua trả góp (installments) qua thẻ tín dụng.
*   **Boleto Bancário (Hóa đơn ngân hàng):** Chiếm **17.9%** tổng giá trị. Đây là phương thức thanh toán tiền mặt phổ biến tại Brazil cho những người không có thẻ ngân hàng.
*   **Voucher và Debit Card:** Chiếm tỷ lệ rất nhỏ (lần lượt là 2.4% và 1.4%).

![Cơ cấu phương thức thanh toán](plots/payment_methods_share.png)

---

## 3. Đề xuất Giải pháp Chiến lược (Business Recommendations)

Dựa trên các kết quả phân tích trên, Olist nên triển khai các hành động chiến lược sau để cải thiện hiệu quả kinh doanh:

1.  **Xây dựng chương trình khách hàng thân thiết (CRM & Loyalty Program):**
    *   Với tỷ lệ khách hàng quay lại cực kỳ thấp (3.04%), Olist cần chủ động gửi các chương trình khuyến mãi, mã giảm giá cho đơn hàng thứ 2 ngay sau khi đơn hàng thứ 1 hoàn thành thành công.
    *   Tập trung khuyến khích khách hàng mua lại ở các ngành hàng có chu kỳ tiêu dùng ngắn như *Health Beauty* (ngành hàng đứng đầu cả về doanh thu và số lượng đơn).

2.  **Tối ưu hóa Logistics tại các vùng xa (Đông Bắc - AL, MA, PI, CE):**
    *   Tỷ lệ trễ đơn tại các bang Đông Bắc lên tới 15 - 24%. Olist cần hợp tác với các đơn vị vận chuyển nội địa có mạng lưới mạnh hơn ở vùng này hoặc thiết lập các kho trung chuyển (Fulfillment Centers) gần khu vực tiêu thụ để giảm thiểu thời gian giao hàng.
    *   Giảm thời gian ước tính hiển thị trên web một cách hợp lý để tránh làm nản lòng khách hàng ở các bang xa, nhưng đồng thời phải kiểm soát chặt chẽ cam kết giao hàng đúng hạn để bảo vệ điểm số review của khách hàng.

3.  **Tối ưu hóa Chi phí vận chuyển (Freight Subsidy):**
    *   Chi phí vận chuyển chiếm tới hơn 14% tổng chi tiêu của khách hàng là rào cản lớn đối với việc mua sắm lặp lại. Olist nên cân nhắc các chính sách hỗ trợ phí ship (ví dụ: Freeship cho đơn hàng giá trị cao từ 150 BRL trở lên) hoặc đàm phán phí vận chuyển tốt hơn với các hãng đối tác nhờ sản lượng đơn hàng lớn.

4.  **Tối ưu hóa các chương trình Trả góp (Credit Card Installments):**
    *   Vì Credit Card chiếm đến 78.4% tổng giá trị thanh toán, Olist cần làm việc sát sao với các cổng thanh toán để cung cấp các gói trả góp không lãi suất (hoặc lãi suất thấp) linh hoạt hơn, đặc biệt đối với các danh mục hàng có giá trị cao như *Watches Gifts* hay *Computers Accessories*.
