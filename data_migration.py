import sqlite3

# 텍스트 파일을 읽어온 후 데이터베이스에 넣는 함수
def insert_data_from_file(filename):
    # 텍스트 파일 열기
    with open(filename, 'r') as file:
        lines = file.readlines()  # 파일의 각 줄을 읽어옴
        
        # SQLite3 연결 생성
        conn = sqlite3.connect('customer_management.db')
        c = conn.cursor()

        results = {}
        names = {}
        # 파일의 각 줄을 순회하면서 데이터 추출 및 데이터베이스에 삽입
        for line in lines:
            if line.strip():  # 빈 줄이 아닌 경우에만 처리
                data = line.split()  # 공백을 기준으로 데이터 분리
                if len(data) < 4:
                    continue
                name = data[1]
                phone = data[0]
                formatted_phone = '-'.join([phone[:3], phone[3:7], phone[7:]])
                mileage = float(data[3])
                
                refusal_status = '거부됨' if name in ('김보미', '이경은', '김나은') else ''
                
                if name not in list(names.keys()):
                    names[name] = 0
                else:
                    names[name] += 1
                    name = name + str(names[name])
                    
                if formatted_phone not in list(results.keys()):
                    results[formatted_phone] = [name, formatted_phone, mileage, refusal_status]
                else:
                    results[formatted_phone][2] += mileage
                    if refusal_status == '거부됨':
                        results[formatted_phone][3] = '거부됨'
                
                print(data)
        
        # 데이터베이스에 삽입
        for key, value in results.items():
            c.execute('''INSERT INTO customers (name, phone, mileage, refusal_status) VALUES (?, ?, ?, ?)''', (value[0], value[1], value[2], value[3]))
        
        # 변경 사항 저장 및 연결 종료
        conn.commit()
        conn.close()

# 텍스트 파일 이름 지정
filename = 'test.txt'

# 데이터베이스에 데이터 삽입
insert_data_from_file(filename)