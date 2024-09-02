import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from Bio import Entrez
import numpy as np
from collections import Counter


# Streamlit 앱 설정
st.set_page_config(page_title="화장품 기업 연구 트렌드 분석", layout="wide")

# 필요한 함수 정의
def search_and_extract(company, start_year, current_year):
    Entrez.email = "nakcho.choi@gmail.com"  # 여기에 실제 이메일 주소를 입력하세요
    query = f'("{company}"[Affiliation]) AND (cosmetics OR skincare OR "skin care" OR beauty OR dermatology) AND ("{start_year}"[PDAT] : "{current_year}"[PDAT])'
    
    # 검색 수행
    handle = Entrez.esearch(db="pubmed", term=query, retmax=5000)
    record = Entrez.read(handle)
    handle.close()
    
    id_list = record["IdList"]
    
    # 데이터 추출
    data = []
    for pmid in id_list:
        handle = Entrez.efetch(db="pubmed", id=pmid, rettype="medline", retmode="xml")
        record = Entrez.read(handle)['PubmedArticle'][0]
        handle.close()
        
        article = record['MedlineCitation']['Article']
        year = article.get('Journal', {}).get('JournalIssue', {}).get('PubDate', {}).get('Year', '')
        
        mesh_headings = record['MedlineCitation'].get('MeshHeadingList', [])
        keywords = "; ".join([mh['DescriptorName'] for mh in mesh_headings if 'DescriptorName' in mh])
        
        if year and year.isdigit():
            data.append({"PY": int(year), "DE": keywords})
    
    return pd.DataFrame(data)

def analyze_keyword_trends(data, company_name):
    yearly_keywords = (data.assign(DE=data['DE'].str.split('; '))
                       .explode('DE')
                       .groupby(['PY', 'DE'])
                       .size()
                       .reset_index(name='count')
                       .sort_values(['PY', 'count'], ascending=[True, False]))
    
    top_keywords = (yearly_keywords.groupby('DE')['count']
                    .sum()
                    .nlargest(10)
                    .index
                    .tolist())
    
    trend_data = yearly_keywords[yearly_keywords['DE'].isin(top_keywords)]
    
    return trend_data

# 메인 앱
def main():
    st.title("화장품 기업 연구 트렌드 분석")
    
    # 사용자 입력
    companies = st.multiselect("분석할 기업 선택:", ["Shiseido", "L'Oreal", "Cosmax"], default=["Shiseido"])
    
    current_year = pd.Timestamp.now().year
    start_year = current_year - 9
    
    if st.button("분석 시작"):
        for company in companies:
            st.subheader(f"{company} 분석")
            
            # 데이터 추출 및 분석
            data = search_and_extract(company, start_year, current_year)
            trend_data = analyze_keyword_trends(data, company)
            
            # 논문 수 표시
            st.write(f"총 논문 수: {len(data)}")
            
            # 키워드 트렌드 그래프
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.lineplot(data=trend_data, x='PY', y='count', hue='DE', ax=ax)
            ax.set_title(f"{company} - Top 10 Keyword Trends Over Time")
            ax.set_xlabel("Year")
            ax.set_ylabel("Frequency")
            plt.xticks(rotation=45)
            st.pyplot(fig)
            
            # 워드클라우드
            all_keywords = ' '.join(data['DE'].dropna())
            wordcloud = WordCloud(width=800, height=400, background_color='white').generate(all_keywords)
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
            
    st.write("## 결론")
    st.write("이 분석을 통해 각 기업의 연구 트렌드와 주요 키워드를 파악할 수 있습니다. 이를 바탕으로 향후 연구 방향을 설정하고 경쟁력을 강화할 수 있습니다.")

if __name__ == "__main__":
    main()