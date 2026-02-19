@echo off
echo ========================================
echo  Sharp Sports Analysis - NFL Analytics Lab
echo ========================================
echo.
echo Installing dependencies...
python -m pip install -q duckdb polars pyarrow streamlit plotly pandas numpy scipy scikit-learn
echo.
echo Launching app...
python -m streamlit run app\Home.py
pause
