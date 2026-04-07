import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# загрузка данных
df = pd.read_csv("voice_features.csv")

st.title("Voice Analysis Dashboard")

# список признаков
features = [col for col in df.columns if col not in ["sex"]]

# dropdown
selected_feature = st.selectbox(
    "Выберите признак",
    features
)

# разделение по полу
split_sex = st.checkbox("Разделить по полу")

# распределение
st.subheader("Распределение")

if split_sex:
    fig = px.histogram(
        df,
        x=selected_feature,
        color="sex",
        marginal="box",
        nbins=50
    )
else:
    fig = px.histogram(
        df,
        x=selected_feature,
        marginal="box",
        nbins=50
    )

st.plotly_chart(fig)

# boxplot
st.subheader("Boxplot")

if split_sex:
    fig_box = px.box(
        df,
        x="sex",
        y=selected_feature,
        points="outliers"
    )
else:
    fig_box = px.box(
        df,
        y=selected_feature,
        points="outliers"
    )

st.plotly_chart(fig_box)

# корреляция
st.subheader("Корреляционная матрица")

corr = df[features].corr()

fig_corr = px.imshow(
    corr,
    text_auto=True,
    aspect="auto"
)

st.plotly_chart(fig_corr)
