# services/advanced_analytics_service.py
"""
Advanced Analytics Service - Senior Data Analyst Techniques
Enterprise-level data analysis, profiling, and ML-powered insights
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import warnings

warnings.filterwarnings('ignore')


class AdvancedAnalyticsService:
    """
    Professional enterprise-level data analysis techniques.
    Goes beyond basic analytics with ML, statistical modeling, and AI insights.
    """
    
    # ================================================================
    # 1. COMPREHENSIVE DATA PROFILING
    # ================================================================
    
    @staticmethod
    def comprehensive_data_profile(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Deep data profiling like a senior data analyst.
        Analyzes distributions, correlations, outliers, and data quality.
        """
        profile = {
            "overview": {},
            "distributions": {},
            "correlations": {},
            "outliers": {},
            "data_quality": {},
            "recommendations": []
        }
        
        # Overview statistics
        profile["overview"] = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024**2,
            "duplicate_rows": df.duplicated().sum(),
            "duplicate_percentage": (df.duplicated().sum() / len(df) * 100) if len(df) > 0 else 0
        }
        
        # Analyze each column
        for col in df.columns:
            col_profile = AdvancedAnalyticsService._profile_column(df[col])
            profile["distributions"][col] = col_profile
        
        # Correlation analysis (numeric columns only)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            
            # Find strong correlations
            strong_correlations = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_value = corr_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:
                        strong_correlations.append({
                            "column1": corr_matrix.columns[i],
                            "column2": corr_matrix.columns[j],
                            "correlation": round(corr_value, 3),
                            "strength": "strong positive" if corr_value > 0 else "strong negative"
                        })
            
            profile["correlations"] = {
                "matrix": corr_matrix.to_dict(),
                "strong_correlations": strong_correlations
            }
        
        # Outlier detection
        for col in numeric_cols:
            outliers = AdvancedAnalyticsService._detect_outliers(df[col])
            if outliers["count"] > 0:
                profile["outliers"][col] = outliers
        
        # Data quality assessment
        profile["data_quality"] = AdvancedAnalyticsService._assess_data_quality(df)
        
        # Generate professional recommendations
        profile["recommendations"] = AdvancedAnalyticsService._generate_recommendations(profile)
        
        return profile
    
    @staticmethod
    def _profile_column(series: pd.Series) -> Dict[str, Any]:
        """Profile a single column comprehensively"""
        profile = {
            "dtype": str(series.dtype),
            "missing_count": int(series.isna().sum()),
            "missing_percentage": round((series.isna().sum() / len(series) * 100), 2),
            "unique_count": int(series.nunique()),
            "unique_percentage": round((series.nunique() / len(series) * 100), 2)
        }
        
        # For numeric columns
        if pd.api.types.is_numeric_dtype(series):
            profile.update({
                "mean": float(series.mean()) if not series.isna().all() else None,
                "median": float(series.median()) if not series.isna().all() else None,
                "std": float(series.std()) if not series.isna().all() else None,
                "min": float(series.min()) if not series.isna().all() else None,
                "max": float(series.max()) if not series.isna().all() else None,
                "q25": float(series.quantile(0.25)) if not series.isna().all() else None,
                "q75": float(series.quantile(0.75)) if not series.isna().all() else None,
                "skewness": float(series.skew()) if not series.isna().all() else None,
                "kurtosis": float(series.kurtosis()) if not series.isna().all() else None
            })
        
        # For categorical columns
        elif pd.api.types.is_object_dtype(series) or pd.api.types.is_categorical_dtype(series):
            value_counts = series.value_counts()
            profile.update({
                "most_common": str(value_counts.index[0]) if len(value_counts) > 0 else None,
                "most_common_count": int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                "most_common_percentage": round((value_counts.iloc[0] / len(series) * 100), 2) if len(value_counts) > 0 else 0
            })
        
        return profile
    
    @staticmethod
    def _detect_outliers(series: pd.Series) -> Dict[str, Any]:
        """Detect outliers using IQR method"""
        if not pd.api.types.is_numeric_dtype(series) or series.isna().all():
            return {"count": 0, "percentage": 0, "method": "IQR"}
        
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = series[(series < lower_bound) | (series > upper_bound)]
        
        return {
            "count": len(outliers),
            "percentage": round((len(outliers) / len(series) * 100), 2),
            "lower_bound": float(lower_bound),
            "upper_bound": float(upper_bound),
            "method": "IQR (Interquartile Range)"
        }
    
    @staticmethod
    def _assess_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive data quality assessment"""
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isna().sum().sum()
        
        quality_score = 100 - (missing_cells / total_cells * 100) if total_cells > 0 else 0
        
        return {
            "overall_score": round(quality_score, 2),
            "total_cells": total_cells,
            "missing_cells": int(missing_cells),
            "completeness": round((1 - missing_cells/total_cells) * 100, 2) if total_cells > 0 else 0,
            "consistency": AdvancedAnalyticsService._check_consistency(df),
            "validity": AdvancedAnalyticsService._check_validity(df)
        }
    
    @staticmethod
    def _check_consistency(df: pd.DataFrame) -> Dict[str, Any]:
        """Check data consistency"""
        issues = []
        
        # Check for mixed data types in object columns
        for col in df.select_dtypes(include=['object']).columns:
            types_found = df[col].dropna().apply(type).unique()
            if len(types_found) > 1:
                issues.append(f"Column '{col}' has mixed data types")
        
        return {
            "score": 100 - (len(issues) * 10),
            "issues": issues
        }
    
    @staticmethod
    def _check_validity(df: pd.DataFrame) -> Dict[str, Any]:
        """Check data validity"""
        issues = []
        
        # Check for negative values where they shouldn't be
        for col in df.select_dtypes(include=[np.number]).columns:
            if 'price' in col.lower() or 'quantity' in col.lower() or 'amount' in col.lower():
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    issues.append(f"Column '{col}' has {negative_count} negative values")
        
        return {
            "score": 100 - (len(issues) * 10),
            "issues": issues
        }
    
    @staticmethod
    def _generate_recommendations(profile: Dict[str, Any]) -> List[str]:
        """Generate professional data quality recommendations"""
        recommendations = []
        
        # Check data quality score
        quality_score = profile["data_quality"]["overall_score"]
        if quality_score < 70:
            recommendations.append("⚠️ Data quality is below acceptable threshold. Consider data cleaning.")
        
        # Check for high missing data
        for col, dist in profile["distributions"].items():
            if dist["missing_percentage"] > 30:
                recommendations.append(f"🔴 Column '{col}' has {dist['missing_percentage']}% missing data - consider imputation or removal.")
        
        # Check for outliers
        if profile["outliers"]:
            recommendations.append(f"📊 {len(profile['outliers'])} columns have outliers - review for data entry errors or valid extremes.")
        
        # Check correlations
        if "strong_correlations" in profile.get("correlations", {}):
            if len(profile["correlations"]["strong_correlations"]) > 0:
                recommendations.append(f"🔗 Found {len(profile['correlations']['strong_correlations'])} strong correlations - consider feature engineering.")
        
        return recommendations
    
    # ================================================================
    # 2. STATISTICAL ANALYSIS
    # ================================================================
    
    @staticmethod
    def statistical_tests(df: pd.DataFrame, target_col: str = None) -> Dict[str, Any]:
        """
        Perform statistical hypothesis tests.
        Professional-grade statistical analysis.
        """
        results = {
            "normality_tests": {},
            "correlation_tests": {},
            "anova": None
        }
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        # Normality tests (Shapiro-Wilk)
        for col in numeric_cols:
            if df[col].notna().sum() > 3:  # Need at least 3 values
                try:
                    statistic, p_value = stats.shapiro(df[col].dropna())
                    results["normality_tests"][col] = {
                        "test": "Shapiro-Wilk",
                        "statistic": float(statistic),
                        "p_value": float(p_value),
                        "is_normal": p_value > 0.05,
                        "interpretation": "Normally distributed" if p_value > 0.05 else "Not normally distributed"
                    }
                except:
                    pass
        
        # Correlation significance tests
        if len(numeric_cols) >= 2:
            for i, col1 in enumerate(numeric_cols):
                for col2 in numeric_cols[i+1:]:
                    try:
                        corr, p_value = stats.pearsonr(
                            df[col1].dropna(),
                            df[col2].dropna()
                        )
                        if abs(corr) > 0.3:  # Only report meaningful correlations
                            results["correlation_tests"][f"{col1}_vs_{col2}"] = {
                                "correlation": float(corr),
                                "p_value": float(p_value),
                                "significant": p_value < 0.05,
                                "strength": AdvancedAnalyticsService._correlation_strength(corr)
                            }
                    except:
                        pass
        
        return results
    
    @staticmethod
    def _correlation_strength(corr: float) -> str:
        """Interpret correlation strength"""
        abs_corr = abs(corr)
        if abs_corr >= 0.7:
            return "Strong"
        elif abs_corr >= 0.4:
            return "Moderate"
        elif abs_corr >= 0.2:
            return "Weak"
        else:
            return "Very weak"
    
    # ================================================================
    # 3. CUSTOMER SEGMENTATION (ML-POWERED)
    # ================================================================
    
    @staticmethod
    def customer_segmentation(df: pd.DataFrame, n_clusters: int = 4) -> Dict[str, Any]:
        """
        ML-powered customer segmentation using K-Means clustering.
        Premium/Ultra Premium feature.
        """
        # Prepare features for clustering
        feature_cols = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['revenue', 'quantity', 'amount', 'total', 'count']):
                if pd.api.types.is_numeric_dtype(df[col]):
                    feature_cols.append(col)
        
        if len(feature_cols) < 2:
            return {"error": "Insufficient numeric features for segmentation"}
        
        # Prepare data
        X = df[feature_cols].dropna()
        if len(X) < n_clusters:
            return {"error": f"Need at least {n_clusters} samples for {n_clusters} clusters"}
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # K-Means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        
        # Analyze clusters
        cluster_analysis = []
        for i in range(n_clusters):
            cluster_data = df.loc[X.index[clusters == i]]
            cluster_analysis.append({
                "cluster_id": i,
                "size": int((clusters == i).sum()),
                "percentage": round((clusters == i).sum() / len(clusters) * 100, 2),
                "characteristics": AdvancedAnalyticsService._describe_cluster(cluster_data, feature_cols)
            })
        
        return {
            "n_clusters": n_clusters,
            "features_used": feature_cols,
            "cluster_analysis": cluster_analysis,
            "silhouette_score": float(AdvancedAnalyticsService._calculate_silhouette(X_scaled, clusters))
        }
    
    @staticmethod
    def _describe_cluster(cluster_df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, Any]:
        """Describe cluster characteristics"""
        description = {}
        for col in feature_cols:
            if pd.api.types.is_numeric_dtype(cluster_df[col]):
                description[col] = {
                    "mean": float(cluster_df[col].mean()),
                    "median": float(cluster_df[col].median()),
                    "total": float(cluster_df[col].sum())
                }
        return description
    
    @staticmethod
    def _calculate_silhouette(X: np.ndarray, labels: np.ndarray) -> float:
        """Calculate silhouette score for clustering quality"""
        from sklearn.metrics import silhouette_score
        try:
            return silhouette_score(X, labels)
        except:
            return 0.0
    
    # ================================================================
    # 4. ANOMALY DETECTION
    # ================================================================
    
    @staticmethod
    def detect_anomalies(df: pd.DataFrame, sensitivity: float = 2.5) -> Dict[str, Any]:
        """
        ML-powered anomaly detection using statistical methods.
        Premium/Ultra Premium feature.
        """
        anomalies = {
            "total_anomalies": 0,
            "anomalies_by_column": {},
            "anomaly_rows": []
        }
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            # Z-score method
            mean = df[col].mean()
            std = df[col].std()
            
            if std > 0:
                z_scores = np.abs((df[col] - mean) / std)
                col_anomalies = df[z_scores > sensitivity].index.tolist()
                
                if len(col_anomalies) > 0:
                    anomalies["anomalies_by_column"][col] = {
                        "count": len(col_anomalies),
                        "percentage": round(len(col_anomalies) / len(df) * 100, 2),
                        "rows": col_anomalies[:10]  # First 10
                    }
                    anomalies["total_anomalies"] += len(col_anomalies)
        
        return anomalies
    
    # ================================================================
    # 5. TREND ANALYSIS & FORECASTING
    # ================================================================
    
    @staticmethod
    def trend_analysis(df: pd.DataFrame, date_col: str, value_col: str) -> Dict[str, Any]:
        """
        Time series trend analysis with forecasting.
        Premium/Ultra Premium feature.
        """
        try:
            # Ensure date column is datetime
            if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
                df[date_col] = pd.to_datetime(df[date_col])
            
            # Sort by date
            df_sorted = df.sort_values(date_col)
            
            # Calculate trend
            x = np.arange(len(df_sorted))
            y = df_sorted[value_col].values
            
            # Linear regression for trend
            slope, intercept = np.polyfit(x, y, 1)
            trend_line = slope * x + intercept
            
            # Calculate metrics
            trend_direction = "Increasing" if slope > 0 else "Decreasing" if slope < 0 else "Flat"
            
            return {
                "trend_direction": trend_direction,
                "slope": float(slope),
                "intercept": float(intercept),
                "r_squared": float(np.corrcoef(y, trend_line)[0, 1] ** 2),
                "forecast_next_3_periods": [
                    float(slope * (len(df_sorted) + i) + intercept) for i in range(1, 4)
                ]
            }
        except Exception as e:
            return {"error": str(e)}
