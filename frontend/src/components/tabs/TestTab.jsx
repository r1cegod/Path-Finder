import React, { useState } from 'react';
import { Brain, ArrowRight, ArrowLeft, BrainCircuit } from 'lucide-react';
import { submitTest } from '../../api/test.js';

const MI_QUESTIONS = [
  // NATURALIST
  {id:"nat_1",  section:"naturalist",    text:"Tôi thích phân loại mọi thứ theo đặc điểm chung"},
  {id:"nat_2",  section:"naturalist",    text:"Các vấn đề sinh thái rất quan trọng với tôi"},
  {id:"nat_3",  section:"naturalist",    text:"Phân loại giúp tôi hiểu dữ liệu mới dễ hơn"},
  {id:"nat_4",  section:"naturalist",    text:"Tôi thích làm vườn"},
  {id:"nat_5",  section:"naturalist",    text:"Tôi cho rằng bảo tồn thiên nhiên là điều quan trọng"},
  {id:"nat_6",  section:"naturalist",    text:"Sắp xếp mọi thứ theo thứ bậc giúp tôi hiểu rõ hơn"},
  {id:"nat_7",  section:"naturalist",    text:"Động vật đóng vai trò quan trọng trong cuộc sống của tôi"},
  {id:"nat_8",  section:"naturalist",    text:"Nhà tôi có hệ thống tái chế"},
  {id:"nat_9",  section:"naturalist",    text:"Tôi thích học sinh học, thực vật học hoặc động vật học"},
  {id:"nat_10", section:"naturalist",    text:"Tôi nhận ra sự khác biệt tinh tế trong ý nghĩa của từ ngữ"},
  // MUSICAL
  {id:"mus_1",  section:"musical",       text:"Tôi dễ dàng nhận ra các mẫu âm nhạc"},
  {id:"mus_2",  section:"musical",       text:"Tôi chú ý đến âm thanh và tiếng động xung quanh"},
  {id:"mus_3",  section:"musical",       text:"Tôi dễ dàng di chuyển theo nhịp điệu"},
  {id:"mus_4",  section:"musical",       text:"Tôi thích tạo ra âm nhạc"},
  {id:"mus_5",  section:"musical",       text:"Tôi cảm nhận được nhịp điệu của thơ ca"},
  {id:"mus_6",  section:"musical",       text:"Tôi ghi nhớ mọi thứ bằng cách đặt chúng vào bài thơ vần"},
  {id:"mus_7",  section:"musical",       text:"Khó tập trung khi có tiếng ồn nền"},
  {id:"mus_8",  section:"musical",       text:"Nghe âm thanh thiên nhiên giúp tôi thư giãn"},
  {id:"mus_9",  section:"musical",       text:"Nhạc kịch cuốn hút tôi hơn kịch nói"},
  {id:"mus_10", section:"musical",       text:"Tôi dễ dàng nhớ lời bài hát"},
  // LOGICAL
  {id:"log_1",  section:"logical",       text:"Tôi được biết đến là người gọn gàng và có trật tự"},
  {id:"log_2",  section:"logical",       text:"Hướng dẫn từng bước rất hữu ích với tôi"},
  {id:"log_3",  section:"logical",       text:"Giải quyết vấn đề đến với tôi một cách tự nhiên"},
  {id:"log_4",  section:"logical",       text:"Tôi dễ bực bội với những người thiếu tổ chức"},
  {id:"log_5",  section:"logical",       text:"Tôi có thể tính toán nhanh trong đầu"},
  {id:"log_6",  section:"logical",       text:"Câu đố logic rất thú vị"},
  {id:"log_7",  section:"logical",       text:"Tôi cần chuẩn bị đầy đủ mới bắt đầu làm việc"},
  {id:"log_8",  section:"logical",       text:"Cấu trúc và trật tự là điều tốt"},
  {id:"log_9",  section:"logical",       text:"Tôi thích tìm hiểu tại sao thứ gì đó không hoạt động"},
  {id:"log_10", section:"logical",       text:"Mọi thứ phải có lý hoặc tôi sẽ không hài lòng"},
  // EXISTENTIAL
  {id:"exi_1",  section:"existential",   text:"Quan trọng với tôi là thấy được vai trò của mình trong bức tranh lớn"},
  {id:"exi_2",  section:"existential",   text:"Tôi thích thảo luận về các câu hỏi về cuộc sống"},
  {id:"exi_3",  section:"existential",   text:"Tôn giáo hoặc tâm linh quan trọng với tôi"},
  {id:"exi_4",  section:"existential",   text:"Tôi thích chiêm ngưỡng tác phẩm nghệ thuật"},
  {id:"exi_5",  section:"existential",   text:"Thiền định và thư giãn rất bổ ích với tôi"},
  {id:"exi_6",  section:"existential",   text:"Tôi thích đi đến những nơi truyền cảm hứng"},
  {id:"exi_7",  section:"existential",   text:"Tôi thích đọc các nhà triết học"},
  {id:"exi_8",  section:"existential",   text:"Học điều mới dễ hơn khi tôi thấy ứng dụng thực tế"},
  {id:"exi_9",  section:"existential",   text:"Tôi tự hỏi liệu có các dạng sống thông minh khác trong vũ trụ"},
  {id:"exi_10", section:"existential",   text:"Quan trọng với tôi là cảm thấy kết nối với người khác và ý tưởng"},
  // INTERPERSONAL
  {id:"int_1",  section:"interpersonal", text:"Tôi học tốt nhất khi tương tác với người khác"},
  {id:"int_2",  section:"interpersonal", text:"Tôi thích cả trò chuyện bình thường lẫn thảo luận nghiêm túc"},
  {id:"int_3",  section:"interpersonal", text:"Càng đông người càng vui"},
  {id:"int_4",  section:"interpersonal", text:"Tôi thường đóng vai trò lãnh đạo trong nhóm"},
  {id:"int_5",  section:"interpersonal", text:"Tôi coi trọng các mối quan hệ hơn thành tích"},
  {id:"int_6",  section:"interpersonal", text:"Học nhóm rất hiệu quả với tôi"},
  {id:"int_7",  section:"interpersonal", text:"Tôi là người chơi đồng đội"},
  {id:"int_8",  section:"interpersonal", text:"Bạn bè rất quan trọng với tôi"},
  {id:"int_9",  section:"interpersonal", text:"Tôi tham gia nhiều hơn 3 câu lạc bộ hoặc tổ chức"},
  {id:"int_10", section:"interpersonal", text:"Tôi không thích làm việc một mình"},
  // KINESTHETIC
  {id:"kin_1",  section:"kinesthetic",   text:"Tôi học bằng cách làm"},
  {id:"kin_2",  section:"kinesthetic",   text:"Tôi thích làm đồ thủ công"},
  {id:"kin_3",  section:"kinesthetic",   text:"Thể thao là một phần cuộc sống của tôi"},
  {id:"kin_4",  section:"kinesthetic",   text:"Tôi dùng cử chỉ khi giao tiếp"},
  {id:"kin_5",  section:"kinesthetic",   text:"Thị phạm tốt hơn giải thích"},
  {id:"kin_6",  section:"kinesthetic",   text:"Tôi thích nhảy múa"},
  {id:"kin_7",  section:"kinesthetic",   text:"Tôi thích làm việc với công cụ"},
  {id:"kin_8",  section:"kinesthetic",   text:"Không hoạt động khiến tôi mệt mỏi hơn bận rộn"},
  {id:"kin_9",  section:"kinesthetic",   text:"Các hoạt động thực hành rất thú vị"},
  {id:"kin_10", section:"kinesthetic",   text:"Tôi có lối sống năng động"},
  // VERBAL
  {id:"ver_1",  section:"verbal",        text:"Tôi quan tâm đến ngôn ngữ nước ngoài"},
  {id:"ver_2",  section:"verbal",        text:"Tôi thích đọc sách, tạp chí và trang web"},
  {id:"ver_3",  section:"verbal",        text:"Tôi giữ nhật ký"},
  {id:"ver_4",  section:"verbal",        text:"Trò chơi ô chữ rất thú vị"},
  {id:"ver_5",  section:"verbal",        text:"Ghi chú giúp tôi nhớ và hiểu tốt hơn"},
  {id:"ver_6",  section:"verbal",        text:"Tôi thường liên lạc bạn bè qua thư hoặc email"},
  {id:"ver_7",  section:"verbal",        text:"Tôi dễ dàng giải thích ý tưởng cho người khác"},
  {id:"ver_8",  section:"verbal",        text:"Tôi viết lách như một sở thích"},
  {id:"ver_9",  section:"verbal",        text:"Chơi chữ và câu đố ngôn từ rất thú vị"},
  {id:"ver_10", section:"verbal",        text:"Tôi thích thuyết trình và tranh luận"},
  // INTRAPERSONAL
  {id:"itr_1",  section:"intrapersonal", text:"Thái độ của tôi ảnh hưởng đến cách tôi học"},
  {id:"itr_2",  section:"intrapersonal", text:"Tôi thích tham gia vào các hoạt động giúp đỡ cộng đồng"},
  {id:"itr_3",  section:"intrapersonal", text:"Tôi rất ý thức về niềm tin đạo đức của mình"},
  {id:"itr_4",  section:"intrapersonal", text:"Tôi học tốt nhất khi có sự gắn kết cảm xúc với chủ đề"},
  {id:"itr_5",  section:"intrapersonal", text:"Công bằng là điều quan trọng với tôi"},
  {id:"itr_6",  section:"intrapersonal", text:"Các vấn đề công bằng xã hội thu hút tôi"},
  {id:"itr_7",  section:"intrapersonal", text:"Làm việc một mình có thể hiệu quả như làm nhóm"},
  {id:"itr_8",  section:"intrapersonal", text:"Tôi cần biết lý do tại sao trước khi đồng ý làm gì đó"},
  {id:"itr_9",  section:"intrapersonal", text:"Khi tin vào điều gì, tôi nỗ lực nhiều hơn"},
  {id:"itr_10", section:"intrapersonal", text:"Tôi sẵn sàng phản đối để bảo vệ điều đúng"},
  // VISUAL
  {id:"vis_1",  section:"visual",        text:"Sắp xếp lại phòng và trang trí nội thất rất thú vị"},
  {id:"vis_2",  section:"visual",        text:"Tôi thích tạo ra tác phẩm nghệ thuật của riêng mình"},
  {id:"vis_3",  section:"visual",        text:"Sơ đồ trực quan giúp tôi nhớ tốt hơn"},
  {id:"vis_4",  section:"visual",        text:"Tôi thích các phương tiện giải trí đa dạng"},
  {id:"vis_5",  section:"visual",        text:"Biểu đồ và bảng biểu giúp tôi phân tích dữ liệu"},
  {id:"vis_6",  section:"visual",        text:"Video âm nhạc khiến tôi thêm yêu thích một bài hát"},
  {id:"vis_7",  section:"visual",        text:"Tôi có thể hình dung mọi thứ như hình ảnh trong đầu"},
  {id:"vis_8",  section:"visual",        text:"Tôi đọc bản đồ và bản vẽ kỹ thuật tốt"},
  {id:"vis_9",  section:"visual",        text:"Câu đố 3D rất thú vị"},
  {id:"vis_10", section:"visual",        text:"Tôi có thể hình dung ý tưởng trong tâm trí"}
];

const RIASEC_QUESTIONS = [
  // REALISTIC
  {index:1,  area:"R", text:"Xây tường hoặc lát gạch"},
  {index:2,  area:"R", text:"Sửa chữa thiết bị gia dụng"},
  {index:3,  area:"R", text:"Nuôi cá tại trại nuôi trồng thủy sản"},
  {index:4,  area:"R", text:"Lái xe tải giao hàng"},
  {index:5,  area:"R", text:"Kiểm tra chất lượng sản phẩm trước khi xuất xưởng"},
  {index:6,  area:"R", text:"Sửa chữa và lắp đặt khóa cửa"},
  {index:7,  area:"R", text:"Vận hành máy móc để sản xuất sản phẩm"},
  {index:8,  area:"R", text:"Chữa cháy rừng"},
  {index:9,  area:"R", text:"Đóng tủ bếp bằng gỗ"},
  {index:10, area:"R", text:"Lắp ráp các linh kiện điện tử"},
  // INVESTIGATIVE
  {index:11, area:"I", text:"Phát triển thuốc mới"},
  {index:12, area:"I", text:"Nghiên cứu cách giảm ô nhiễm nguồn nước"},
  {index:13, area:"I", text:"Thực hiện các thí nghiệm hóa học"},
  {index:14, area:"I", text:"Nghiên cứu chuyển động của các hành tinh"},
  {index:15, area:"I", text:"Phân tích mẫu máu qua kính hiển vi"},
  {index:16, area:"I", text:"Điều tra nguyên nhân vụ cháy"},
  {index:17, area:"I", text:"Phát triển phương pháp dự báo thời tiết chính xác hơn"},
  {index:18, area:"I", text:"Làm việc trong phòng thí nghiệm sinh học"},
  {index:19, area:"I", text:"Phát minh chất thay thế đường"},
  {index:20, area:"I", text:"Xét nghiệm để chẩn đoán bệnh"},
  // ARTISTIC
  {index:21, area:"A", text:"Viết sách hoặc kịch bản"},
  {index:22, area:"A", text:"Chơi nhạc cụ"},
  {index:23, area:"A", text:"Sáng tác hoặc phối khí âm nhạc"},
  {index:24, area:"A", text:"Vẽ tranh"},
  {index:25, area:"A", text:"Tạo hiệu ứng đặc biệt cho phim"},
  {index:26, area:"A", text:"Thiết kế bối cảnh sân khấu"},
  {index:27, area:"A", text:"Viết kịch bản phim hoặc truyền hình"},
  {index:28, area:"A", text:"Biểu diễn nhảy jazz hoặc tap"},
  {index:29, area:"A", text:"Hát trong ban nhạc"},
  {index:30, area:"A", text:"Biên tập phim"},
  // SOCIAL
  {index:31, area:"S", text:"Hướng dẫn cá nhân về bài tập thể dục"},
  {index:32, area:"S", text:"Giúp đỡ người có vấn đề tâm lý"},
  {index:33, area:"S", text:"Tư vấn định hướng nghề nghiệp"},
  {index:34, area:"S", text:"Thực hiện liệu pháp phục hồi chức năng"},
  {index:35, area:"S", text:"Tình nguyện tại tổ chức phi lợi nhuận"},
  {index:36, area:"S", text:"Dạy trẻ em chơi thể thao"},
  {index:37, area:"S", text:"Dạy ngôn ngữ ký hiệu cho người khiếm thính"},
  {index:38, area:"S", text:"Hỗ trợ buổi trị liệu nhóm"},
  {index:39, area:"S", text:"Chăm sóc trẻ tại nhà trẻ"},
  {index:40, area:"S", text:"Giảng dạy tại trường trung học"},
  // ENTERPRISING
  {index:41, area:"E", text:"Mua bán cổ phiếu và trái phiếu"},
  {index:42, area:"E", text:"Quản lý cửa hàng bán lẻ"},
  {index:43, area:"E", text:"Điều hành salon tóc"},
  {index:44, area:"E", text:"Quản lý phòng ban trong công ty lớn"},
  {index:45, area:"E", text:"Khởi nghiệp kinh doanh"},
  {index:46, area:"E", text:"Đàm phán hợp đồng kinh doanh"},
  {index:47, area:"E", text:"Đại diện pháp lý cho khách hàng"},
  {index:48, area:"E", text:"Marketing dòng sản phẩm thời trang mới"},
  {index:49, area:"E", text:"Bán hàng tại trung tâm thương mại"},
  {index:50, area:"E", text:"Quản lý cửa hàng quần áo"},
  // CONVENTIONAL
  {index:51, area:"C", text:"Xây dựng bảng tính bằng phần mềm máy tính"},
  {index:52, area:"C", text:"Soát lỗi hồ sơ và biểu mẫu"},
  {index:53, area:"C", text:"Cài đặt phần mềm vào mạng máy tính lớn"},
  {index:54, area:"C", text:"Vận hành máy tính"},
  {index:55, area:"C", text:"Ghi chép xuất nhập kho"},
  {index:56, area:"C", text:"Tính toán tiền lương nhân viên"},
  {index:57, area:"C", text:"Kiểm kê hàng tồn kho bằng thiết bị cầm tay"},
  {index:58, area:"C", text:"Ghi nhận các khoản thanh toán"},
  {index:59, area:"C", text:"Quản lý hồ sơ tồn kho"},
  {index:60, area:"C", text:"Phân loại và phân phối thư từ"}
];

export default function TestTab({ sessionId, onStateUpdate, appState }) {
  const [currentView, setCurrentView] = useState('cards');
  const [miAnswers, setMiAnswers] = useState({});
  const [riasecAnswers, setRiasecAnswers] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Derived from real state — survives tab switches
  const miSubmitted = appState?.thinking?.brain_type != null;
  const riasecSubmitted = appState?.thinking?.riasec_top != null;

  const handleMiAnswer = (id, value) => {
    setMiAnswers(prev => ({ ...prev, [id]: value }));
  };

  const handleMiSubmit = async () => {
    const scores = {};
    MI_QUESTIONS.forEach(q => {
      if (!scores[q.section]) scores[q.section] = 0;
      if (miAnswers[q.id] === 1) scores[q.section] += 10;
    });
    const brain_type = Object.keys(scores).filter(section => scores[section] >= 80);
    setIsSubmitting(true);
    try {
      await submitTest(sessionId, { brain_type }, onStateUpdate);
      setCurrentView('cards');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRiasecAnswer = (index, value) => {
    setRiasecAnswers(prev => ({ ...prev, [index]: value }));
  };

  const handleRiasecSubmit = async () => {
    const scores = {};
    RIASEC_QUESTIONS.forEach(q => {
      if (!scores[q.area]) scores[q.area] = 0;
      scores[q.area] += riasecAnswers[q.index] || 0;
    });
    const areaScores = Object.keys(scores).map(area => ({
      area,
      score: (scores[area] / 50) * 100,
    }));
    areaScores.sort((a, b) => b.score - a.score);
    const riasec_top = areaScores.slice(0, 2).map(a => a.area);
    setIsSubmitting(true);
    try {
      await submitTest(sessionId, { riasec_top }, onStateUpdate);
      setCurrentView('cards');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={`flex-1 px-6 py-4 ${currentView === 'cards' ? 'overflow-hidden' : 'overflow-y-auto [&::-webkit-scrollbar]:hidden'} `} style={{ scrollbarWidth: 'none' }}>
      {currentView === 'cards' && (
        <div className="max-w-4xl mx-auto space-y-6 pb-8">
          {/* Card 1: Personality Assessment */}
          <div
            className={`bg-[#111111] border border-[#1e1e1e] rounded-lg p-6 flex flex-col gap-6 transition-colors ${riasecSubmitted ? 'opacity-60 cursor-default' : 'hover:border-[#7C3AED]/50 cursor-pointer group'}`}
            onClick={() => !riasecSubmitted && setCurrentView('personality-quiz')}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-[#131313] border border-[#1e1e1e] rounded flex items-center justify-center">
                  <Brain className="text-primary w-6 h-6" />
                </div>
                {riasecSubmitted ? (
                  <div className="px-3 py-1 bg-[#10B981]/10 border border-[#10B981]/30 rounded-full">
                    <span className="text-[10px] font-bold text-[#10B981] uppercase tracking-wider">HOÀN THÀNH</span>
                  </div>
                ) : (
                  <div className="px-3 py-1 bg-[#7C3AED]/10 border border-[#7C3AED]/30 rounded-full">
                    <span className="text-[10px] font-bold text-[#7C3AED] uppercase tracking-wider">SẴN SÀNG</span>
                  </div>
                )}
              </div>
              {!riasecSubmitted && <ArrowRight className="text-zinc-600 group-hover:text-primary transition-colors w-6 h-6" />}
            </div>
            <div>
              <h3 className="text-[18px] font-bold text-white mb-2">Đánh giá Tính cách (RIASEC)</h3>
              <p className="text-[13px] text-[#a0a0a0] leading-relaxed w-full">
                Bài kiểm tra dựa trên mô hình Holland Codes (RIASEC) giúp phân tích sâu sắc các mẫu hành vi cốt lõi, sở thích nghề nghiệp và động lực xã hội tiềm ẩn. Từ đó xác định nhóm tính cách của bạn: Thực tế (R), Nghiên cứu (I), Nghệ thuật (A), Xã hội (S), Khởi nghiệp (E) hoặc Truyền thống (C).
              </p>
            </div>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">THỜI GIAN DỰ KIẾN</span>
              <span className="text-[10px] font-mono text-zinc-400">12P</span>
            </div>
          </div>

          {/* Card 2: Brain & Learning Mode */}
          <div
            className={`bg-[#111111] border border-[#1e1e1e] rounded-lg p-6 flex flex-col gap-6 transition-colors ${miSubmitted ? 'opacity-60 cursor-default' : 'hover:border-[#7C3AED]/50 cursor-pointer group'}`}
            onClick={() => !miSubmitted && setCurrentView('brain-quiz')}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-[#131313] border border-[#1e1e1e] rounded flex items-center justify-center">
                  <BrainCircuit className="text-primary w-6 h-6" />
                </div>
                {miSubmitted ? (
                  <div className="px-3 py-1 bg-[#10B981]/10 border border-[#10B981]/30 rounded-full">
                    <span className="text-[10px] font-bold text-[#10B981] uppercase tracking-wider">HOÀN THÀNH</span>
                  </div>
                ) : (
                  <div className="px-3 py-1 bg-[#7C3AED]/10 border border-[#7C3AED]/30 rounded-full">
                    <span className="text-[10px] font-bold text-[#7C3AED] uppercase tracking-wider">SẴN SÀNG</span>
                  </div>
                )}
              </div>
              {!miSubmitted && <ArrowRight className="text-zinc-600 group-hover:text-primary transition-colors w-6 h-6" />}
            </div>
            <div>
              <h3 className="text-[18px] font-bold text-white mb-2">Chế độ Não bộ & Tư duy (Brain Test)</h3>
              <p className="text-[13px] text-[#a0a0a0] leading-relaxed w-full">
                Bài kiểm tra dựa trên Thuyết Đa Trí Tuệ (Multiple Intelligences) giúp lập bản đồ điểm mạnh nhận thức của bạn qua các dạng tư duy khác nhau (ví dụ: tư duy hình ảnh, logic - toán học, ngôn ngữ, thiên nhiên, âm nhạc, vận động...). Từ đó tìm ra môi trường học tập và làm việc tối ưu nhất.
              </p>
            </div>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">THỜI GIAN DỰ KIẾN</span>
              <span className="text-[10px] font-mono text-zinc-400">08P</span>
            </div>
          </div>

          {/* Decorative Element */}
          <div className="pt-8 flex flex-col items-center justify-center opacity-20 select-none pointer-events-none">
            <div className="flex items-center gap-4 mb-4">
              <div className="h-px w-24 bg-gradient-to-r from-transparent to-zinc-500"></div>
              <span className="text-[10px] font-mono tracking-[0.4em] text-zinc-500 uppercase">Đang chờ lựa chọn...</span>
              <div className="h-px w-24 bg-gradient-to-l from-transparent to-zinc-500"></div>
            </div>
            <div className="grid grid-cols-4 gap-2">
              <div className="w-1 h-1 bg-zinc-700"></div>
              <div className="w-1 h-1 bg-zinc-800"></div>
              <div className="w-1 h-1 bg-zinc-700"></div>
              <div className="w-1 h-1 bg-zinc-800"></div>
            </div>
          </div>
        </div>
      )}

      {currentView === 'brain-quiz' && (
        <div className="max-w-3xl mx-auto space-y-4 pb-8">
          <div className="mb-6 flex items-center justify-between">
            <button 
              onClick={() => setCurrentView('cards')}
              className="group flex items-center gap-2 text-[#555] hover:text-zinc-300 transition-all duration-200 py-1"
            >
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
              <span className="text-xs font-medium uppercase tracking-widest">Quay lại</span>
            </button>
            <span className="text-xs font-mono text-zinc-500">{Object.keys(miAnswers).length} / 90 câu hỏi</span>
          </div>

          <div className="bg-[#7C3AED]/10 border border-[#7C3AED]/20 rounded-lg p-5 mb-8">
            <h2 className="text-[#7C3AED] font-medium mb-2">Về bài đánh giá Đa trí tuệ (Multiple Intelligences)</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              Bài trắc nghiệm này giúp khám phá thiên hướng tư duy nổi trội của bạn (ví dụ: Không gian - Thị giác, Tự nhiên, Logic - Toán học, Ngôn ngữ...). Hiểu rõ cách não bộ hoạt động tốt nhất sẽ giúp bạn tìm ra phương pháp học tập và giải quyết vấn đề hiệu quả nhất.
            </p>
          </div>
          
          {MI_QUESTIONS.map(q => {
            const isAgree = miAnswers[q.id] === 1;
            const isSkip = miAnswers[q.id] === 0;
            
            return (
              <div key={q.id} className="bg-[#111111] border border-[#1e1e1e] rounded-lg p-6">
                <h3 className="font-sans text-[16px] font-medium text-white mb-5">{q.text}</h3>
                <div className="flex flex-row gap-4">
                  <button 
                    onClick={() => handleMiAnswer(q.id, 1)}
                    className={`rounded-full px-6 py-2 font-semibold text-sm transition-colors ${
                      isAgree 
                        ? 'bg-[#10B981] text-white border border-[#10B981]' 
                        : 'bg-[#10B981]/10 border border-[#10B981] text-[#10B981] hover:bg-[#10B981]/20'
                    }`}
                  >
                    Đồng ý
                  </button>
                  <button 
                    onClick={() => handleMiAnswer(q.id, 0)}
                    className={`rounded-full px-6 py-2 text-sm transition-all ${
                      isSkip
                        ? 'bg-[#171717] border border-zinc-500 text-zinc-300'
                        : 'bg-[#171717] border border-[#2a2a2a] text-[#555] hover:text-zinc-300 hover:border-zinc-500'
                    }`}
                  >
                    Bỏ qua
                  </button>
                </div>
              </div>
            );
          })}
          
          <button
            onClick={handleMiSubmit}
            disabled={Object.keys(miAnswers).length < 90 || isSubmitting}
            className={`w-full bg-[#7C3AED] text-white rounded-lg py-3 font-semibold mt-8 transition-all ${
              Object.keys(miAnswers).length < 90 || isSubmitting ? 'opacity-50 cursor-not-allowed' : 'hover:brightness-110'
            }`}
          >
            {isSubmitting ? 'Đang nộp...' : 'Nộp bài'}
          </button>
        </div>
      )}

      {currentView === 'personality-quiz' && (
        <div className="max-w-3xl mx-auto space-y-12 pb-8">
          <div className="mb-8 flex items-center justify-between">
            <button 
              onClick={() => setCurrentView('cards')}
              className="flex items-center gap-2 px-0 py-2 text-[#555555] hover:text-zinc-300 transition-colors group"
            >
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
              <span className="text-[11px] font-medium uppercase tracking-[0.15em] font-mono">Quay lại</span>
            </button>
            <span className="text-xs font-mono text-zinc-500">{Object.keys(riasecAnswers).length} / 60 câu hỏi</span>
          </div>

          <div className="bg-[#10B981]/10 border border-[#10B981]/20 rounded-lg p-5 mb-8 -mt-4">
            <h2 className="text-[#10B981] font-medium mb-2">Về bài đánh giá RIASEC (Holland Codes)</h2>
            <p className="text-sm text-zinc-400 leading-relaxed">
              Mô hình Holland phân loại tính cách thành 6 nhóm: Kỹ thuật, Nghiên cứu, Nghệ thuật, Xã hội, Quản lý, và Nghiệp vụ. Bằng cách đánh giá ấn tượng của bạn với các hoạt động khác nhau, hệ thống sẽ phác họa biểu đồ tính cách và gợi ý các môi trường làm việc phù hợp nhất.
            </p>
          </div>
          
          {RIASEC_QUESTIONS.map(q => {
            const val = riasecAnswers[q.index];
            
            return (
              <div key={q.index} className="pb-10 border-b border-white/5">
                <h3 className="font-sans text-[16px] font-medium text-zinc-200 mb-8">{q.text}</h3>
                <div className="flex items-center justify-between gap-4 w-full">
                  <span className="text-[11px] text-zinc-500 font-medium uppercase tracking-wider w-28 text-right">Ấn tượng tốt</span>
                  <div className="flex items-center justify-center gap-4 lg:gap-8 flex-1">
                    {/* 5 */}
                    <div 
                      onClick={() => handleRiasecAnswer(q.index, 5)}
                      className={`likert-circle w-12 h-12 border-[#10B981] ${val === 5 ? 'bg-[#10B981] opacity-100' : ''}`}
                    ></div>
                    {/* 4 */}
                    <div 
                      onClick={() => handleRiasecAnswer(q.index, 4)}
                      className={`likert-circle w-10 h-10 border-[#10B981]/60 ${val === 4 ? 'bg-[#10B981]/60 opacity-100' : ''}`}
                    ></div>
                    {/* 3 */}
                    <div 
                      onClick={() => handleRiasecAnswer(q.index, 3)}
                      className={`likert-circle w-7 h-7 border-zinc-600 ${val === 3 ? 'bg-zinc-600 opacity-100' : ''}`}
                    ></div>
                    {/* 2 */}
                    <div 
                      onClick={() => handleRiasecAnswer(q.index, 2)}
                      className={`likert-circle w-10 h-10 border-[#7C3AED]/60 ${val === 2 ? 'bg-[#7C3AED]/60 opacity-100' : ''}`}
                    ></div>
                    {/* 1 */}
                    <div 
                      onClick={() => handleRiasecAnswer(q.index, 1)}
                      className={`likert-circle w-12 h-12 border-[#7C3AED] ${val === 1 ? 'bg-[#7C3AED] opacity-100' : ''}`}
                    ></div>
                  </div>
                  <span className="text-[11px] text-zinc-500 font-medium uppercase tracking-wider w-28">Ấn tượng xấu</span>
                </div>
              </div>
            );
          })}
          
          <button
            onClick={handleRiasecSubmit}
            disabled={Object.keys(riasecAnswers).length < 60 || isSubmitting}
            className={`w-full bg-[#7C3AED] text-white rounded-lg py-3 font-semibold mt-8 transition-all ${
              Object.keys(riasecAnswers).length < 60 || isSubmitting ? 'opacity-50 cursor-not-allowed' : 'hover:brightness-110'
            }`}
          >
            {isSubmitting ? 'Đang nộp...' : 'Nộp bài'}
          </button>
        </div>
      )}
    </div>
  );
}
