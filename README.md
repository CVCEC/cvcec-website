# cvcec.org: website của CVCEC

Website tĩnh của **Canada Vietnam Cultural & Educational Council (CVCEC)**, chạy miễn phí trên GitHub Pages từ thư mục `docs/`. Các đường dẫn cũ từ Webador đều được giữ nguyên (ví dụ `/about`, `/programs/viet-youth-readiness-hub`, các bài tin `/news-media/3348082_...`), nên link cũ, kết quả Google và các bài đã chia sẻ vẫn mở được.

## Thư mục nào chứa gì

| Thư mục / file | Nội dung |
|---|---|
| `src/pages/` | Mỗi trang một file. Phần trên dấu `---` là tiêu đề (title), mô tả (description) và ảnh chia sẻ (image); phần dưới là nội dung trang. |
| `src/pages/programs/` | Các trang chương trình: Trường Tiếng Việt, PEI Branch, VYRH, Readiness & Safety Initiative, Leading Urban Change, Mentoring Program. |
| `src/posts/` | Mỗi bài tin một file. |
| `src/assets/` | Màu sắc và kiểu chữ (`site.css`), menu, phóng to ảnh, form liên hệ (`site.js`), logo (`logo-mark.webp`), favicon. |
| `build.py` | Ghép `src/` thành website hoàn chỉnh trong `docs/`. Menu và chân trang nằm trong file này. |
| `docs/` | Website hoàn chỉnh mà GitHub Pages hiển thị. **Không sửa trực tiếp**, vì mỗi lần build sẽ ghi đè. |
| `docs/images/` | Ảnh gốc. Bản nhẹ (WebP) nằm trong `docs/images/w/` và được dùng tự động. |

## Hai ngôn ngữ: tiếng Anh và tiếng Việt

- Bản tiếng Anh ở địa chỉ gốc (`/about`, `/programs/pei-branch`…). Bản tiếng Việt có cùng địa chỉ nhưng thêm `/vi` ở đầu (`/vi/about`, `/vi/programs/pei-branch`…). Nút **Tiếng Việt / English** trên menu chuyển qua lại giữa hai bản.
- Chữ tiếng Việt nằm trong `src/i18n/vi/`, mỗi trang một file `.json` (ví dụ `programs__pei-branch.json`, bài tin là `post__3348082.json`). Mỗi dòng có dạng `"câu tiếng Anh": "câu tiếng Việt"`.
- **Sửa chữ tiếng Việt:** mở file `.json` của trang, chỉ sửa phần sau dấu hai chấm (câu tiếng Việt), giữ nguyên dấu ngoặc kép và các thẻ như `<strong>`, `<a href="…">`. Commit, rồi chạy build.
- **Sửa chữ tiếng Anh:** khi bạn sửa một câu tiếng Anh trong `src/pages/`, câu đó ở bản tiếng Việt sẽ tạm hiện bằng tiếng Anh cho tới khi có bản dịch mới. Cách nhanh nhất là nhờ Claude: "cập nhật bản dịch tiếng Việt cho trang …".
- Chữ trên menu và chân trang tiếng Việt nằm trong `build.py`, ở danh sách `UI_VI`.

## Sửa chữ trên một trang

1. Trên GitHub, mở `src/pages/` rồi chọn file của trang cần sửa (ví dụ `programs/pei-branch.html`).
2. Bấm biểu tượng bút chì (Edit). Chỉ sửa phần chữ nằm giữa các thẻ, ví dụ `<p>…</p>` hoặc `<h2>…</h2>`, không xoá các dấu `<` `>`.
3. Bấm **Commit changes**.
4. Chạy build (xem mục "Chạy build" bên dưới), hoặc nhờ Claude chạy giúp.

## Thêm một bài tin mới

1. Mở `src/posts/`, mở một bài có sẵn, bấm **Raw** rồi sao chép toàn bộ nội dung.
2. Bấm **Add file → Create new file**. Đặt tên theo mẫu `số_tieu-de-khong-dau.html`, ví dụ `3400000_cvcec-hosts-vietnamese-culture-day.html`. Số đầu tên file nên lớn hơn các bài cũ.
3. Dán nội dung, rồi sửa các dòng `title`, `seo_title`, `date` (dạng `2026-11-25`), `description`, `summary`, `image` và phần thân bài.
4. Ảnh của bài: tải ảnh vào `docs/images/` (mục tiếp theo), rồi trong bài ghi `@/ten-anh.jpg`.
5. Commit, rồi chạy build. Bài mới tự hiện ở trang chủ và trang News.

## Thêm ảnh vào Gallery

1. Mở `docs/images/`, bấm **Add file → Upload files**, kéo ảnh vào rồi Commit. Nên đặt tên ảnh không dấu, không khoảng trắng.
2. Mở `src/pages/news-media/gallery.html`, tìm album muốn thêm ảnh, chép một dòng có sẵn và đổi tên ảnh:
   `<a href="@/ten-anh.jpg"><img src="@/ten-anh.jpg" alt="Mô tả ngắn bằng tiếng Anh"></a>`
3. Muốn tạo album mới thì chép cả khối `<div class="album">…</div>` và đổi tiêu đề trong `<h3>`.
4. Commit, rồi chạy build.

## Chạy build

Cách đơn giản nhất là nhờ Claude: "chạy build cho repo cvcec-website". Nếu máy tính của bạn có Python thì chạy:

- Bản xem thử, không cho Google tìm thấy: `PREVIEW=1 SITE_BASE=/cvcec-website/ python3 build.py`
- Bản chính thức, sau khi đã trỏ tên miền: `python3 build.py`

Sau khi commit, GitHub Pages tự cập nhật trong 1–2 phút.

## Form liên hệ (Formspree)

Form ở trang Contact gửi thư về contact@cvcec.org qua Formspree (gói miễn phí). Form có sẵn một ô ẩn để chặn spam.

1. Đăng nhập formspree.io bằng contact@cvcec.org, tạo một form mới và chép mã form (dạng `xyzabcde`).
2. Trong `src/pages/contact.html`, thay `YOUR_FORM_ID` bằng mã đó. Commit, rồi chạy build.

Khi chưa thay mã, nút **Send message** sẽ mở ứng dụng email của người gửi thay cho Formspree.

## Chuyển tên miền cvcec.org về GitHub

1. Trong repo này, vào **Settings → Pages → Custom domain**, nhập `www.cvcec.org` rồi bấm **Save**. GitHub sẽ tự tạo file `docs/CNAME`.
2. Ở Nhân Hòa (nơi quản lý DNS của cvcec.org), chỉ sửa các bản ghi của website:
   - `@`: 4 bản ghi A trỏ tới `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `www`: CNAME trỏ tới `cvcec.github.io`
   - **Không động vào** MX (email Google Workspace), các bản ghi TXT xác minh, và các tên miền con như `duhoccanada`, `vietclass`, `pei`, `workshops`, `vietnamday`.
3. Khi GitHub báo chứng chỉ đã sẵn sàng, tích ô **Enforce HTTPS**.
4. Chạy build bản chính thức (`python3 build.py`) để Google được phép tìm thấy website, rồi gửi `https://www.cvcec.org/sitemap.xml` lên Google Search Console.
