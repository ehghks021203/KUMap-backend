# 쿠맵(KUMap) API 사용 가이드

## 쿠맵(KUMap) API 에러코드 설명 및 조치 방안
|범주|err_code|코드값|설명|조치방안|
|---|---|---|---|---|
|all|00|Success|요청이 성공적으로 처리되었습니다.|별도의 조치 필요 없음|
|request|10|Invalid JSON Format|리퀘스트의 형식이 JSON이 아닙니다.|요청의 Content-Type을 확인하고, JSON 형식으로 요청하세요.|
|request|11|Missing Parameter|필수 파라미터가 누락되었습니다.|모든 필수 파라미터가 포함되었는지 확인하세요.|
|request|12|Invalid Email Format|이메일 형식이 올바르지 않습니다.|이메일 형식을 확인하고 올바른 형식으로 입력하세요.|
|request|13|Invalid Nickname Format|닉네임 형식이 올바르지 않거나 길이가 부적절합니다.|닉네임 형식과 길이를 확인하세요.|
|request|14|Invalid Password Format|비밀번호 형식이나 길이가 부적절합니다.|비밀번호 형식과 길이를 확인하고 규칙에 맞게 설정하세요.|
|auth|20|	User Not Found|요청한 유저 정보를 찾을 수 없습니다.|유저 정보가 정확한지 확인하고, 다시 시도하세요.|
|auth|21|User Already Exists|해당 유저가 이미 존재합니다.|다른 이메일 또는 닉네임을 사용해 보세요.|
|auth|22|Incorrect Password|입력한 비밀번호가 올바르지 않습니다.|비밀번호를 다시 확인하고, 올바르게 입력하세요.|
|auth|23|Duplicate Nickname|이미 사용중인 닉네임입니다.|다른 닉네임을 선택하여 다시 시도하세요.|
|data|30|Data Not Found|요청한 데이터를 찾을 수 없습니다.|데이터의 존재 여부를 확인하고, 정확한 요청을 보내세요.|
|server|100|Commit Error|데이터베이스 커밋 중 오류가 발생했습니다.|데이터베이스 연결을 확인하고, 다시 시도하세요.|

