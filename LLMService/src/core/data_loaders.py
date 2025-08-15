# LLM을 사용할 떄 필요한 데이터를 제공하는 클래스
# task, 즉 프롬프트마다 필요한 데이터가 다를 수 있고 요구에 따라 데이터를 db나 jsonl 등 에서 가져와야함
# user prompt에서 포메팅에 필요한 데이터도 여기서 가져오도록
# JsonlDataLoader, CsvDataLoader, DBDataLoader ...
# 현재는 방송인의 메타데이터, 플랫폼의 메타데이터 용도로 ./LLMService/data 임시저장소를 사용예정
# https://python.langchain.com/docs/integrations/document_loaders/json/ 참고
