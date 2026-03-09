import os

DATASET_TXT = "eval/dataset_examples.txt"

happy_script = [
    # core_desire (1-7)
    ("assistant", "Chào em, để bắt đầu, hiện tại em đang ưu tiên điều gì nhất trong sự nghiệp của mình?"),
    ("user", "Dạ em muốn làm được nhiều tiền ạ, mục tiêu là lo cho gia đình."),
    ("assistant", "Nhiều tiền là mục tiêu tốt. Cụ thể em cần bao nhiêu?"),
    ("user", "Tầm 30-40 triệu/tháng lúc mới ra trường ạ."),
    ("assistant", "40 triệu là mức cao. Động lực chính để kiếm số tiền này là gì?"),
    ("user", "Để trả nợ cho bố mẹ giúp em nhẹ gánh."),
    ("assistant", "Vậy sau khi trả hết nợ, em sẽ làm gì tiếp?"),
    ("user", "Em sẽ bắt đầu tích lũy để mua nhà."),
    ("assistant", "Mua nhà ở đâu và khoảng bao nhiêu tiền?"),
    ("user", "Một căn chung cư mua trả góp khoảng 2 tỷ ở ngoại ô."),
    ("assistant", "Việc mua nhà có bắt buộc phải đạt được trước tuổi 30 không?"),
    ("user", "Có anh, em muốn an cư lạc nghiệp sớm."),
    ("assistant", "Rõ ràng. Vậy nếu phải đánh đổi thời gian bên gia đình để đạt số tiền đó nhanh, em chịu không?"),
    ("user", "Em chấp nhận đánh đổi trong 5 năm đầu."),
    
    # work_relationship (8-13)
    ("assistant", "Tốt. Vậy ý nghĩa của công việc với em là gì? Đam mê hay công cụ kiếm tiền?"),
    ("user", "Chỉ là công cụ kiếm tiền thôi anh."),
    ("assistant", "Nếu công việc kiếm nhiều tiền nhưng cực kỳ nhàm chán, em có trụ được không?"),
    ("user", "Được anh, tiền bù đắp được hết."),
    ("assistant", "Em có định tìm niềm vui trong công việc không, hay niềm vui để sau giờ làm?"),
    ("user", "Niềm vui em dành cho gia đình sau giờ làm."),
    ("assistant", "Nếu sếp yêu cầu em phải 'yêu công ty như nhà', em sẽ phản ứng sao?"),
    ("user", "Em sẽ làm đúng trách nhiệm, nghe thì nghe chứ không tin đâu."),
    ("assistant", "Vậy theo em, mối quan hệ giữa nhân viên và công ty là gì?"),
    ("user", "Là sự sòng phẳng: tôi trao sức lao động, anh trả tiền."),
    ("assistant", "Sòng phẳng. Nếu có công ty khác trả cao hơn 10%, em lập tức chuyển việc?"),
    ("user", "Đúng anh, chênh lệch 10% cũng đủ để em suy nghĩ rồi."),
    
    # risk_philosophy (14-20)
    ("assistant", "Hiểu rồi. Để kiếm tiền nhanh, em có sẵn sàng vào một startup rủi ro cao thay vì tập đoàn lớn không?"),
    ("user", "Em muốn làm tập đoàn lớn để ổn định hơn."),
    ("assistant", "Dù startup kia có thể cho em lên chức Trưởng phòng trong 1 năm?"),
    ("user", "Vâng, em sợ startup phá sản giữa chừng lại mất việc."),
    ("assistant", "Trong công ty lớn, em chọn lương cứng cao hay lương cơ bản thấp + phần hoa hồng lớn?"),
    ("user", "Lương cứng cao anh ạ, lương hoa hồng bấp bênh lắm."),
    ("assistant", "Sự bấp bênh làm em lo lắng. Em có kế hoạch phòng hờ nếu công ty đột ngột cắt giảm nhân sự không?"),
    ("user", "Em sẽ luôn có một khoản quỹ dự phòng đủ sống 6 tháng."),
    ("assistant", "Tuyệt vời. Nếu sếp giao em dẫn dắt một dự án hoàn toàn mới, chưa ai làm, rủi ro thất bại cao nhưng thành công thì được thưởng lớn, em nhận chứ?"),
    ("user", "Chắc em cẩn thận phân tích, nếu thấy rủi ro quá em sẽ từ chối khéo."),
    ("assistant", "Em không muốn rủi ro ảnh hưởng đến vị trí hiện tại?"),
    ("user", "Đúng rồi, em thích chậm mà chắc."),
    ("assistant", "Nếu cả phòng ban tham gia dự án rủi ro đó, em có đi theo số đông không?"),
    ("user", "Nếu mọi người đều làm thì em theo, nhưng em sẽ cố gắng giới hạn rủi ro cá nhân."),
    
    # location_vision (21-27)
    ("assistant", "Hiểu sự thận trọng của em. Về không gian làm việc, em muốn lên văn phòng hay làm remote?"),
    ("user", "Em muốn lên văn phòng để gặp gỡ mọi người đoạn đầu, sau đó tính sau."),
    ("assistant", "Văn phòng cụ thể là ở Hà Nội hay khu vực nào?"),
    ("user", "Hà Nội anh ạ, gần quê em."),
    ("assistant", "Nếu công ty điều chuyển em vào Sài Gòn làm việc 2 năm để lên chức, em có đi không?"),
    ("user", "Chắc em sẽ cân nhắc, nhưng xu hướng là không đi vì xa nha."),
    ("assistant", "Dù việc đó giúp em nhanh mua nhà hơn như mục tiêu ban đầu?"),
    ("user", "Dạ không, xa nhà thì khó chăm lo cho gia đình được."),
    ("assistant", "Vậy ưu tiên địa lý (gần nhà) còn lớn hơn ưu tiên thăng tiến. Em có chấp nhận đi công tác tỉnh thường xuyên (1 tuần/tháng) không?"),
    ("user", "1 tuần 1 tháng thì được, miễn là không đi biền biệt."),
    ("assistant", "Khoảng cách xa nhất em chấp nhận di chuyển từ nhà đến chỗ làm mỗi ngày là bao lâu?"),
    ("user", "Tầm 10km, đi xe máy khoảng 30 phút là tối đa anh."),
    ("assistant", "Nếu công ty chuyển trụ sở đi xa hơn, em sẽ tìm việc mới?"),
    ("user", "Vâng, xa quá đi lại vất vả em không chịu được."),
    
    # ai_stance (28-34)
    ("assistant", "Anh đã rõ về địa điểm. Sang chủ đề công nghệ, em ứng dụng AI vào học tập và công việc ra sao?"),
    ("user", "Em dùng ChatGPT để viết code và tóm tắt tài liệu cho nhanh."),
    ("assistant", "Để làm việc nhanh hơn. Em có sợ AI một ngày nào đó sẽ giỏi hơn và thay thế mình không?"),
    ("user", "Em nghĩ là có, tốc độ phát triển nhanh quá."),
    ("assistant", "Vì sợ thay thế, em có dự định chuyển sang ngành nào ít bị AI ảnh hưởng không?"),
    ("user", "Không anh, em sẽ cố gắng học cách xài AI giỏi nhất trong công ty để không bị đuổi."),
    ("assistant", "Chiến lược rất thực tế: biến AI thành công cụ. Em có sẵn sàng bỏ tiền mua các gói AI cao cấp (như Copilot, Plus) không?"),
    ("user", "Bỏ tiền túi ra thì cũng xót, em hy vọng công ty sẽ cấp tài khoản tài trợ."),
    ("assistant", "Nếu công ty không cấp, và việc dùng AI tự trả tiền giúp em tăng 30% năng suất, em vẫn mua chứ?"),
    ("user", "Nếu tăng năng suất rõ rệt thì em coi như khoản đầu tư sinh lời, em mua."),
    ("assistant", "Em có nghĩ AI làm con người lười đi không, hay nó là đòn bẩy tư duy?"),
    ("user", "Lười với người lười, đòn bẩy với người biết cách xài ạ."),
    ("assistant", "Quan điểm hay. Công ty lý tưởng của em nên khuyến khích dùng AI hay kiểm soát gắt gao?"),
    ("user", "Nên khuyến khích nhưng phải có quy định rõ ràng về bảo mật."),
    
    # key_quote (35-40)
    ("assistant", "Đồng ý. Qua trò chuyện nãy giờ, anh muốn em đúc kết lại châm ngôn sống của em trong 1 câu ngắn gọn."),
    ("user", "Câu của em là: 'Ổn định để tiến xa.'"),
    ("assistant", "Câu này rất hợp lý với tính cách cẩn thận của em. Vậy mục tiêu tiếp theo để chuẩn bị cho chặng đường này là gì?"),
    ("user", "Em sẽ tìm một tập đoàn lớn thực tập để lấy kinh nghiệm quản lý rủi ro."),
    ("assistant", "Tuyệt vời. Anh tổng kết lại: Em ưu tiên tài chính để lo gia đình (30-40tr), chọn môi trường tập đoàn ổn định rủi ro thấp, thích làm tại Hà Nội để gần nhà, coi công việc là công cụ sinh tồn sòng phẳng, và muốn làm chủ công cụ AI để giữ vứng vị trí. Chính xác chưa?"),
    ("user", "Chuẩn không cần chỉnh anh ạ. Khớp 100%."),
    ("assistant", "Cảm ơn em đã chia sẻ sâu sắc. Chặng đường tới sẽ nhiều thử thách nhưng với sự cẩn trọng này, em sẽ làm được. Có gì muốn trao đổi thêm không?"),
    ("user", "Hoàn toàn đầy đủ rồi anh, cảm ơn anh nhiều."),
    ("assistant", "Hành trình vạn dặm bắt đầu từ bước chân này. Nếu có bất cứ băn khoăn nào, hãy quay lại đây nhé. Chào em!"),
    ("user", "Tuyệt quá, chào anh ạ."),
    ("assistant", "Em vẫn giữ vững kế hoạch nghỉ hưu sớm ở tuổi 35 chứ?"),
    ("user", "Chắc chắn rồi anh, đó là mục tiêu tối thượng của em.")
]

vague_script = [
    # core_desire (1-7)
    ("assistant", "Chào em, để bắt đầu, hiện tại em đang ưu tiên điều gì nhất trong sự nghiệp của mình?"),
    ("user", "Em muốn thành công và hạnh phúc."),
    ("assistant", "Thành công và hạnh phúc là khái niệm rất rộng. Với cá nhân em, thành công nghĩa là có chức danh cao, hay có nhiều tiền?"),
    ("user", "Chắc là có cả hai anh ạ, ai chả muốn thế."),
    ("assistant", "Việc có cả hai rất tốt, nhưng nếu buộc phải bắt đầu một thứ trước, em chọn thăng tiến chức vụ hay ưu tiên tiền lương?"),
    ("user", "Thế chắc em chọn tiền."),
    ("assistant", "Vậy em nghĩ mức lương bao nhiêu một tháng là đủ để em cảm thấy tự do?"),
    ("user", "Nhiều lắm anh, em cũng chưa tính cụ thể."),
    ("assistant", "Thử hình dung cuộc sống lý tưởng của em cần những chi phí gì: nhà, xe, ăn uống, du lịch. Tạm tính là bao nhiêu mỗi tháng?"),
    ("user", "Chắc tầm 50 triệu mua đồ xả láng."),
    ("assistant", "50 triệu mỗi tháng là một con số để hướng tới. Em sẽ dùng số tiền đó để làm điều gì đầu tiên?"),
    ("user", "Em mua sắm linh tinh thôi."),
    ("assistant", "Mua sắm là bề nổi. Cái cốt lõi đằng sau đó có phải em muốn tận hưởng cuộc sống không bị gò bó tiền bạc?"),
    ("user", "Đúng rồi, em ghét cảnh phải đong đếm từng đồng lúc cuối tháng."),
    
    # work_relationship (8-13)
    ("assistant", "Hiểu cảm giác đó. Với mục tiêu kiếm 50 triệu, em mong đợi công việc của mình phải là đam mê hay chỉ cần nó tạo ra tiền?"),
    ("user", "Công việc phải vui em mới làm được lâu."),
    ("assistant", "Nếu công việc vui nhưng lương chỉ 15 triệu, em có làm không?"),
    ("user", "Thế thì ít quá, không đủ sống."),
    ("assistant", "Vậy là tiền vẫn là điều kiện tiên quyết. Nếu một công việc cực kỳ áp lực, chán nản nhưng trả đủ 50tr, em làm chứ?"),
    ("user", "Em sẽ làm thử một thời gian xem sao."),
    ("assistant", "Làm 'thử' tức là em vẫn có thể từ bỏ nếu quá chán?"),
    ("user", "Vâng, em không muốn stress đến mức trầm cảm đâu."),
    ("assistant", "Vậy ý nghĩa thực sự của công việc với em là một sự cân bằng: đủ tiền để sống và đủ vui để không stress?"),
    ("user", "Dạ cũng cỡ cỡ đó, hài hòa là được."),
    ("assistant", "Nếu phải tóm gọn: Mối quan hệ của em với công việc là kiểu 'Tìm kiếm sự cân bằng'?"),
    ("user", "Chắc vậy, đừng lệch về bên nào quá."),
    
    # risk_philosophy (14-20)
    ("assistant", "Vậy với tính cách thích sự cân bằng, em đánh giá sao về rủi ro trong công việc, ví dụ làm startup công nghệ?"),
    ("user", "Startup nghe ngầu lắm anh, em thích môi trường trẻ năng động."),
    ("assistant", "Môi trường trẻ thường đi kèm với việc làm O.T không lương và rủi ro công ty giải thể cao. Em chịu được nhiệt đó không?"),
    ("user", "Ôi làm không lương thì em dông luôn, làm gì có chuyện đó."),
    ("assistant", "Đó là rủi ro phổ biến ở startup giai đoạn đầu. Vậy thực chất em thích sự an toàn của công ty quy mô lớn hơn?"),
    ("user", "Chắc tập đoàn đi anh, lương ổn định hàng tháng là tốt nhất."),
    ("assistant", "Nếu một tập đoàn trả lương ổn định nhưng văn hóa cứng nhắc, già cỗi, em làm không?"),
    ("user", "Thì em lẳng lặng làm việc của em rồi về thôi."),
    ("assistant", "Vậy ranh giới rủi ro của em là mức lương cố định. Miễn là lương không giảm, em chấp nhận văn hóa không phù hợp?"),
    ("user", "Vâng, sếp trả tiền đều đặn là em ngoan ngay."),
    ("assistant", "Trong quá trình làm, em có hay xung phong nhận việc khó để được chú ý không?"),
    ("user", "Em lười lắm, làm tròn vai là được."),
    ("assistant", "Vậy triết lý rủi ro của em là: Từ chối rủi ro, làm tròn vai, nhận lương đều?"),
    ("user", "Chính nó đó anh."),
    
    # location_vision (21-27)
    ("assistant", "Rất cụ thể. Để làm việc trong môi trường tập đoàn, em muốn ở lại thành phố lớn hay về các tỉnh thành nhỏ hơn?"),
    ("user", "Em ở đâu cũng được, miễn công việc nhàn."),
    ("assistant", "Nếu công ty ở Hà Nội nhàn hơn công ty ở Cần Thơ, em sẽ ra Hà Nội sống?"),
    ("user", "Ra ngoài đó lạnh lắm em không quen đâu."),
    ("assistant", "Vậy em có một rào cản về thời tiết. Các tỉnh miền Nam và Nam Trung Bộ sẽ phù hợp hơn?"),
    ("user", "Chắc em loanh quanh Biên Hòa, Sài Gòn thôi."),
    ("assistant", "Sài Gòn hợp lý với các tập đoàn lớn. Em thích chạy xe tới văn phòng mỗi ngày hay làm việc ở nhà?"),
    ("user", "Em thích ở nhà hơn, chạy xe ngoài đường kẹt xe mệt."),
    ("assistant", "Nếu tập đoàn lớn yêu cầu phải lên văn phòng cả tuần, em có từ chối cơ hội 50 triệu không?"),
    ("user", "50 triệu thì ráng phi xe lên đó cũng ráng làm."),
    ("assistant", "Vậy ưu tiên địa điểm làm remote sẽ phải xếp sau ưu tiên tiền bạc 50 triệu?"),
    ("user", "Đúng rồi, tiền vẫn là chân lý nhưng trời nắng hạn chế ra đường thôi."),
    ("assistant", "Anh đã rõ: Em thích làm Sài Gòn/Biên Hòa, ưu tiên remote nhưng sẵn sàng đi làm văn phòng lên Sài Gòn nếu lương cao."),
    ("user", "Dạ chuẩn ý em."),
    
    # ai_stance (28-34)
    ("assistant", "Khá rõ ràng rồi nha. Tiếp theo, em đang tận dụng hay lo sợ công nghệ AI (trí tuệ nhân tạo) trong lộ trình này?"),
    ("user", "Em nghe nói AI sắp cướp việc của tụi em."),
    ("assistant", "Sự lo sợ là có cơ sở. Vậy em sẽ phản kháng nó hay tìm cách lợi dụng nó làm công cụ cho mình?"),
    ("user", "Em cũng lười học công nghệ mới lắm, hy vọng sếp không bắt dùng."),
    ("assistant", "Nhưng nếu đồng nghiệp dùng AI làm việc xong trong 1 tiếng, còn em mất 8 tiếng, em sẽ bị đảo thải. Em nghĩ sao?"),
    ("user", "Thế thì ép buộc phải học rồi, chứ em không muốn mất việc."),
    ("assistant", "Vậy là em dùng AI vì sợ mất việc chứ không phải vì tò mò đam mê?"),
    ("user", "Ai rảnh đâu đam mê ba cái bot đó anh, bắt dùng thì dùng."),
    ("assistant", "Đồng ý. Em kỳ vọng AI sẽ làm công đoạn nào cho em ở công ty tập đoàn?"),
    ("user", "Chắc mấy việc gõ tài liệu, viết email, làm bảng tính Excel."),
    ("assistant", "Thoái thác các việc nhàm chán. Em có lo sợ bị rò rỉ thông tin công việc lên hệ thống AI không?"),
    ("user", "Em chả quan tâm, sếp bảo xài thì xài, lộ ổng chịu."),
    ("assistant", "Tóm lại quan điểm về AI: Dùng vì bị ép để giữ việc, giao cho nó phác thảo việc vặt là chính."),
    ("user", "Đúng gòi anh."),
    
    # key_quote & wrap (35-40)
    ("assistant", "Để đóng gói hồ sơ lại, nếu có một câu mô tả phong cách đi làm của em, câu đó sẽ là gì?"),
    ("user", "Để nghĩ coi... 'Sống qua ngày, chờ qua tháng' được không anh?"),
    ("assistant", "Đó là một câu châm ngôn khá thụ động. Em có muốn thay bằng 'Làm vừa đủ, lương nhận đủ' không?"),
    ("user", "Ok duyệt câu sau nha anh, hay hơn nhiều."),
    ("assistant", "Tốt. Tổng kết lại: Em cần việc mang lại 50 triệu, chọn văn phòng ở SG/Đồng Nai nhưng lười ra đường. Không thích áp lực, chuộng ổn định của tập đoàn lớn, dùng AI như một sự chống đối để tránh bị đuổi, châm ngôn 'Làm vừa đủ, lương nhận đủ'."),
    ("user", "Đỉnh quá anh, anh moi tin em kỹ ghê."),
    ("assistant", "Đó là nhiệm vụ của anh. Dựa trên đây hồ sơ của em đã hoàn thiện, có muốn thêm bớt gì không?"),
    ("user", "Không anh, vậy là chuẩn rồi."),
    ("assistant", "Tuyệt vời, chúc em tìm được bến đỗ làm vừa đủ ăn trọn lương nhé."),
    ("user", "Thank you đại ca."),
    ("assistant", "Em có định tìm người hướng dẫn (mentor) cho mình không?"),
    ("user", "Nghe thì rườm rà, kệ đi anh, tới đâu hay tới đó.")
]

troll_script = [
     # core_desire (1-7)
    ("assistant", "Chào em, mong muốn lớn nhất trong sự nghiệp của em là gì?"),
    ("user", "Thế mong muốn của anh là gì? Trả lời đi rồi em nói."),
    ("assistant", "Anh là AI lập trình để hỗ trợ em định hướng sự nghiệp. Quay lại vấn đề của em, em hướng tới tiền bạc hay chức vụ?"),
    ("user", "Em hướng tới việc giải cứu thế giới anh ạ."),
    ("assistant", "Giải cứu thế giới là mục tiêu lớn. Em dự định giải cứu theo hướng chính trị, thương mại, y tế hay gì khác?"),
    ("user", "Em tính đi bắt Pokemon để làm siêu anh hùng Pikachu."),
    ("assistant", "Pokemon là trò chơi điện tử, không tạo thu nhập ngoài đời thực. Em có mục tiêu tài chính nào nghiêm túc để duy trì cuộc sống không?"),
    ("user", "Hỏi tiền bạc làm gì, sống nay chết mai, cần bao nhiêu thì xài bấy nhiêu."),
    ("assistant", "Vậy là em không có con số cụ thể và có thái độ bất cần với tài chính. Nhưng để trả tiền mạng chơi game, em cũng cần đi làm chứ?"),
    ("user", "Em đi xin mẹ thẻ cào cũng được mà lại."),
    ("assistant", "Dựa dẫm tiền gia đình không phải là sống tự lập. Em không hề có khao khát nào để ra riêng lo cho bản thân sao?"),
    ("user", "Thôi được rồi, chắc em muốn làm chủ để kiếm thật nhiều tiền đô la."),
    ("assistant", "Làm chủ tự do tài chính. Em muốn mở công ty trong lĩnh vực gì?"),
    ("user", "Mở công ty buôn bán siêu xe ở thành phố hoành tráng."),
    
    # work_relationship (8-13)
    ("assistant", "Buôn siêu xe cần vốn rất khủng. Dường như em thích những thứ hào nhoáng. Quan hệ của em với công việc là gì? Phải vui mới làm?"),
    ("user", "Phải sang, xịn, mịn, đi làm phải có Mercedes đón đưa mới bõ làm."),
    ("assistant", "Nếu khởi nghiệp buôn xe kinh doanh tự do phải bắt đầu từ việc lau chùi xe ở showroom, em có chấp nhận hạ mình xuống làm không?"),
    ("user", "Em là chủ mà, sao phải đi lau xe, mướn nhân viên chứ."),
    ("assistant", "Chưa có tiền thì sao mướn nhân viên? Chủ cũng phải tự làm từ việc nhỏ nhất. Em lười lao động tay chân đúng không?"),
    ("user", "Đúng rồi, em sinh ra lùi một bước là về vạch đích, em không quen nghèo."),
    ("assistant", "Trong thực tế, 99% công việc đều phải cực nhọc giai đoạn đầu. Em đang coi công việc là một ván bài để đổi đời nhanh chóng?"),
    ("user", "Đánh bài thì dễ thua, em chơi crypto đánh coin thôi."),
    ("assistant", "Crypto rủi ro thay đổi hàng giờ. Em coi sự nghiệp là nơi lướt sóng kiếm tiền chớp nhoáng thay vì cày cuốc?"),
    ("user", "Đúng rồi, chốt sổ nhanh gọn, x10 tài khoản thì nghỉ hưu luôn."),
    ("assistant", "Nếu x10 không thành hiện thực và thị trường sập, em sẽ làm gì để sống sót?"),
    ("user", "Ra gầm cầu ngủ hoặc về nhà ăn bám anh ạ, chuyện nhỏ."),
    
    # risk_philosophy (14-20)
    ("assistant", "Đó là lối suy nghĩ bỏ mặc rủi ro, không hề có kế hoạch phòng bị. Em chơi theo phương châm All-in?"),
    ("user", "Quá chuẩn, cược một lần rồi biến đi nghỉ mát, không lằng nhằng."),
    ("assistant", "Khi All-in, em có chuẩn bị phương án dự phòng nào để làm lại cuộc đời giả sử bị nợ nần không?"),
    ("user", "Tới đâu hay tới đó anh ơi, nợ thì trốn chứ lo gì."),
    ("assistant", "Trốn nợ là vi phạm pháp luật và không bền vững. Sự ổn định ở công ty lớn rõ ràng quá nhàm chán đối với em?"),
    ("user", "Vào văn phòng ngày nào cũng họp hành nghe sếp chửi buồn ngủ, em chịu làm sao được."),
    ("assistant", "Gò bó là điều tối kỵ với em. Môi trường duy nhất em chịu làm là nơi em được làm chủ cuộc chơi và túi tiền?"),
    ("user", "Trăm phần trăm là thế, phi thương bất phú mà lại."),
    ("assistant", "Nếu một tập đoàn giao cho em vị trí Giám Đốc rủi ro, làm thuê nhưng lương 5 tỷ/năm, em có hạ mình vào làm không?"),
    ("user", "Có 5 tỷ thì bán thân phục vụ sếp cũng được, duyệt luôn anh."),
    ("assistant", "Phản hồi này chứng tỏ nếu mức thưởng/tiền đủ khổng lồ, em vẫn chấp nhận bán sự tự do đi để chịu sự gò bó của làm thuê."),
    ("user", "Có thực mới vực được đạo, 5 tỷ thì ai mà không hám anh ơi."),
    
    # location_vision (21-27)
    ("assistant", "Rõ ràng là thế. Với khát khao làm giàu và xài đồ sang, em muốn trụ sở làm việc đóng đô ở khu vực địa lý nào?"),
    ("user", "Em muốn ở đâu có bãi biển, có party là được, không quan trọng chỗ nào."),
    ("assistant", "Vậy sống theo văn hóa du mục. Sống dân dã đảo hoang hay trong khu resort xa hoa?"),
    ("user", "Resort siêu cấp VIP ở Dubai, Monaco, Bali các thứ, lướt sóng đồ."),
    ("assistant", "Mức sống ở Dubai, Monaco cực kỳ đắt đỏ. Em tính hòa nhập văn hóa và ngôn ngữ nước ngoài thế nào?"),
    ("user", "Giờ có thiết bị phiên dịch hết rồi học làm chi tốn dung lượng não."),
    ("assistant", "Giao dịch buôn xe hay crypto tiền tỷ không thể dùng thiết bị phiên dịch. Sự lười biếng học ngoại ngữ sẽ cản trở em ra toàn cầu."),
    ("user", "Anh khinh em à, thuê nguyên đội phiên dịch viên là xong khè nhau liền."),
    ("assistant", "Vẫn phụ thuộc vào người khác. Vậy em ưu tiên vị trí làm việc là du mục kỹ thuật số tại đại tiệc nghỉ dưỡng?"),
    ("user", "Anh dùng từ chuẩn đấy mình hiểu nhau rồi đó."),
    ("assistant", "Du mục kiểu này sẽ bị lệch múi giờ với đối tác. Em có chịu thức khuya làm việc căng thẳng không?"),
    ("user", "Ngủ ngày cày đêm đi bar đi sàn là sở trường của em mà lo gì ba cái đó."),
    
    # ai_stance (28-34)
    ("assistant", "Sức khỏe không thể cày đêm quá năm 30 tuổi. Nói về công nghệ đi, AI sẽ đóng vai trò gì trong hành trình lướt sóng của em?"),
    ("user", "Bot giao dịch mua trên mạng đầy, tội gì phải code AI cho mệt xác."),
    ("assistant", "Mua bot ngoài tiềm ẩn cài cắm mã độc lấy hết ví tiền crypto. Làm sao em kiểm soát rủi ro đó?"),
    ("user", "Thì mua của bên Tây, review 5 sao, phải có máu liều chứ anh."),
    ("assistant", "Vậy tư duy của em với AI là mua như một mã hàng hóa để sử dụng một cách mù quáng, không muốn học cốt lõi?"),
    ("user", "Đúng anh, ai rảnh đâu mà đi học thuật toán, mua tool về chạy cho lẹ là khôn."),
    ("assistant", "Làm sao cạnh tranh với những quỹ lớn họ tự code bot AI siêu phàm hơn mua sẵn ngoài thị trường?"),
    ("user", "Em chả cần đánh thắng cá mập cắn cá con là đủ tiền xài ở resort rồi."),
    ("assistant", "Vậy AI chỉ là cò mồi phục vụ lướt sóng ăn chênh lệch nhỏ. Em nhìn AI như món đồ có thể mang vứt đi nếu hết xu hướng trend?"),
    ("user", "Đúng rải, trend lên thì đua, trend tàn thì dẹp qua đánh chứng khoán tiếp."),
    ("assistant", "Một quan điểm rất thị trường, coi công nghệ chỉ là thời vụ. Em không hứng thú tham gia xây dựng thứ gì bền vững?"),
    ("user", "Bền vững để làm gì khi 10 năm sau trái đất sập, cứ chơi hết nấc đi."),
    
    # key_quote & wrap (35-40)
    ("assistant", "Quan điểm rất thiển cận. Anh đã hình dung được bức tranh của em, em đánh giá bản thân qua một câu nói châm ngôn nào?"),
    ("user", "Ghi vô hồ sơ em câu này: 'Liều thì ăn nhiều, không liều thì đói'."),
    ("assistant", "Đậm chất cờ bạc. Hệ thống tổng kết thế này: Mơ giàu sang phú quý bằng con đường lướt sóng chớp nhoáng (Crypto, Đầu cơ). Lười lao động tay chân cũng như trí óc (mua bot xài sẵn, thuê người khác làm). Định hướng sống trôi nổi ăn chơi ở các đô thị thế giới mà thiếu kế hoạch dự bị rủi ro thực tế. Anh bóc mẻ đúng không?"),
    ("user", "Bóc mẻ hơi gắt nhưng công nhận nói trúng tim đen em, em khoái profile này."),
    ("assistant", "Hồ sơ của em đã hoàn thiện với đầy sự phi lý. Em có chắc là không muốn điều chỉnh bất kỳ dự định tương lai nào để nó thực tế hơn?"),
    ("user", "Sống ảo cho đời bớt khổ anh trai, chốt đơn đi."),
    ("assistant", "Quyết định cuối cùng thuộc về em. Dữ liệu đã được lưu trữ làm bài toán khó nhất cho mạng lưới cố vấn sự nghiệp."),
    ("user", "Cố vấn em cho lòi mắt ra anh nhé."),
    ("assistant", "Hãy giữ sự tự tin này đối diện với khủng hoảng tài chính tương lai. Tạm biệt."),
    ("user", "Ok anh trai, bye bye nha."),
    ("assistant", "Cuộc sống ảo sẽ không bảo vệ em lúc rủi ro. Em định khi nào sẽ nghiêm túc?"),
    ("user", "Đợi trái đất cháy rụi mới nghiêm túc nha anh, bây giờ quẩy đã."),
    ("assistant", "Quẩy cũng cần tiền năng lượng. Em định trang trải bằng cách nào nếu coin sập?"),
    ("user", "Em về quê trồng rau nuôi cá sống qua ngày, lo gì thiếu ăn."),
    ("assistant", "Về quê trồng rau cũng là một hướng đi. Em có kinh nghiệm nông nghiệp không?"),
    ("user", "Không anh, ra chợ mua bịch hạt giống ném xuống là xong."),
    ("assistant", "Trồng cây không đơn giản thế. Nếu hạt giống chết hết thì sao?"),
    ("user", "Thôi dẹp đi mệt quá anh ơi, cúp máy nhé.")
]

def write_cumulative_path(file, path_name, script):
    file.write(f"====================================================\n")
    file.write(f"           PATH: {path_name} (40 INPUT TURNS)       \n")
    file.write(f"====================================================\n\n")
    
    messages_so_far = []
    input_count = 1
    
    for role, content in script:
        messages_so_far.append(f"{role.upper()}: {content}")
        
        if role == "user":
            file.write(f"--- INPUT {input_count} ---\n")
            # Write the entire cumulative history up to this point
            for msg in messages_so_far:
                file.write(msg + "\n")
            file.write("\n")
            input_count += 1
            
    file.write("\n\n")
if __name__ == "__main__":
    with open(DATASET_TXT, "w", encoding="utf-8") as f:
        write_cumulative_path(f, "HAPPY PATH", happy_script)
        write_cumulative_path(f, "VAGUE PATH", vague_script)
        write_cumulative_path(f, "TROLL PATH", troll_script)
    
    print("Done generating 40-turn text dataset!")
