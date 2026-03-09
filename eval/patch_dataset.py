import os

FILE_PATH = "eval/generate_txt_dataset.py"

with open(FILE_PATH, "r", encoding="utf-8") as f:
    code = f.read()

happy_add = """    ("assistant", "Em vẫn giữ vững kế hoạch nghỉ hưu sớm ở tuổi 35 chứ?"),
    ("user", "Chắc chắn rồi anh, đó là mục tiêu tối thượng của em.")
]"""

vague_add = """    ("assistant", "Em có định tìm người hướng dẫn (mentor) cho mình không?"),
    ("user", "Nghe thì rườm rà, kệ đi anh, tới đâu hay tới đó.")
]"""

troll_add = """    ("assistant", "Cuộc sống ảo sẽ không bảo vệ em lúc rủi ro. Em định khi nào sẽ nghiêm túc?"),
    ("user", "Đợi trái đất cháy rụi mới nghiêm túc nha anh, bây giờ quẩy đã."),
    ("assistant", "Quẩy cũng cần tiền năng lượng. Em định trang trải bằng cách nào nếu coin sập?"),
    ("user", "Em về quê trồng rau nuôi cá sống qua ngày, lo gì thiếu ăn."),
    ("assistant", "Về quê trồng rau cũng là một hướng đi. Em có kinh nghiệm nông nghiệp không?"),
    ("user", "Không anh, ra chợ mua bịch hạt giống ném xuống là xong."),
    ("assistant", "Trồng cây không đơn giản thế. Nếu hạt giống chết hết thì sao?"),
    ("user", "Thôi dẹp đi mệt quá anh ơi, cúp máy nhé.")
]"""

code = code.replace('    ("user", "Tuyệt quá, chào anh ạ.")\n]', '    ("user", "Tuyệt quá, chào anh ạ."),\\n' + happy_add)
code = code.replace('    ("user", "Thank you đại ca.")\n]', '    ("user", "Thank you đại ca."),\\n' + vague_add)
code = code.replace('    ("user", "Ok anh trai, bye bye nha.")\n]', '    ("user", "Ok anh trai, bye bye nha."),\\n' + troll_add)

code = code.replace('\\n', '\n') # fix the newline escaping i added for the replace above

with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write(code)

print("Patched generate_txt_dataset.py!")
