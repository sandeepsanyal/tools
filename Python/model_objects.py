# importing modules
import numpy as np
import pandas as pd
import statistics as stat
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor


def vif(
        X: pd.core.frame.DataFrame
) -> pd.core.frame.DataFrame:
    """
    Calculates variance inflation factor (VIF), for all variables

    Variance Inflation Factor (VIF) quantifies the severity of multicollinearity in an ordinary least squares regression
    analysis.
    It provides an index that measures how much the variance (the square of the estimate's standard deviation) of an
    estimated regression coefficient is increased because of collinearity

    Parameters
    ----------
    X : Pandas DataFrame
        Design matrix with all explanatory variables, as for example used in regression

    Returns
    -------
    Pandas DataFrame
        Variance inflation factor
    """

    # checking for intercept term. If not, adding intercept
    if 'const' not in X.columns.values.tolist():
        X = sm.add_constant(X)

    # calculating VIF and converting result to a DataFrame
    vif = pd.DataFrame()
    vif["VIF"] = [
        variance_inflation_factor(X.values, i) for i in range(X.shape[1])
    ]
    vif["Variable"] = X.columns
    vif = vif.loc[
        vif['Variable'] != 'const',
        ["Variable", "VIF"]
    ].reset_index(drop=True)
    vif.sort_values(
        by=["VIF"],
        ascending=False,
        inplace=True
    )
    vif.reset_index(
        drop=True,
        inplace=True
    )

    return vif


def model_accuracies(
        df: pd.core.frame.DataFrame,
        dep_var: str,
        indep_vars: list,
        model
):
    """

        Parameters
        ----------
        df : Pandas DataFrame
            design matrix with all explanatory variables, as for example used in regression

        dep_var : string
            column name of the dependent variable

        indep_vars : list
            list of column names of independent variables

        model : statsmodels object. Type = RegressionResultsWrapper
            model equation stored in an object

        Returns
        -------
        A dictionary
            A dictionary of accuracy metrices like MAE, MAPE & WMAPE
        """

    temp_df = df.copy()
    temp_df['predicted'] = model.predict(
        exog=temp_df[indep_vars]
    ).tolist()

    return dict(
        {
            'MAE': round(
                number=stat.mean(
                    np.absolute(
                        temp_df[dep_var] -
                        temp_df['predicted']
                    )
                ),
                ndigits=2
            ),
            'MAPE': round(
                number=stat.mean(
                    (
                            np.absolute(temp_df[dep_var] -
                                        temp_df['predicted']
                                        ) /
                            temp_df['predicted']
                    ) * 100
                ),
                ndigits=2
            ),
            'WMAPE': round(
                number=(
                               np.sum(
                                   np.absolute(
                                       temp_df[dep_var] -
                                       temp_df['predicted']
                                   )
                               ) /
                               np.sum(
                                   temp_df[dep_var]
                               )
                       ) * 100,
                ndigits=2
            )
        }
    )

def model_results(
        model,
        train_data: pd.core.frame.DataFrame,
        test_data: pd.core.frame.DataFrame,
        indep_vars: list,
        dep_var: str,
        export_path: str = None):

    try:
        temp = pd.read_excel(
            io=export_path,
            sheet_name="Sheet1",
            na_values=['#NA','#N/A','',' ','na','NA']
        )
        iter = temp['Iteration Number'].max()+1
    except:
        iter = 1

    result_table = pd.merge(left=pd.DataFrame(
        {
            'Iteration Number': iter,
            'Variable': model.params.index,
            'Estimate': model.params
        }
    ),
        right=pd.DataFrame(
            {
                'Variable': model.pvalues.index,
                'p-value':model.pvalues
            }
        ),
        how='left',
        left_on='Variable',
        right_on='Variable'
    )
    result_table = pd.merge(
        left=result_table,
        right=pd.DataFrame(
            {
                'Variable': model.tvalues.index,
                't-value': model.tvalues
            }
        ),
        how='left',
        left_on='Variable',
        right_on='Variable'
    )
    result_table = pd.merge(
        left=result_table,
        right=vif(
            X=train_data[indep_vars]
        ),
        how='left',
        left_on='Variable',
        right_on='Variable'
    )
    result_table['Adj R-sq'] = model.rsquared_adj
    result_table['Train MAE'] = model_accuracies(
        df=train_data,
        dep_var=dep_var,
        indep_vars=indep_vars,
        model=model
    )['MAE']
    result_table['Train MAPE'] = (
                                     model_accuracies(
                                         df=train_data,
                                         dep_var=dep_var,
                                         indep_vars=indep_vars,
                                         model=model
                                     )['MAPE']
                                 ) / 100
    result_table['Train WMAPE'] = (
                                      model_accuracies(
                                          df=train_data,
                                          dep_var=dep_var,
                                          indep_vars=indep_vars,
                                          model=model
                                      )['WMAPE']
                                  ) / 100
    result_table['Test MAE'] = model_accuracies(
        df=test_data,
        dep_var=dep_var,
        indep_vars=indep_vars,
        model=model
    )['MAE']
    result_table['Test MAPE'] = (
                                        model_accuracies(
                                            df=test_data,
                                            dep_var=dep_var,
                                            indep_vars=indep_vars,
                                            model=model
                                        )['MAPE']
                                ) / 100
    result_table['Test WMAPE'] = (
                                     model_accuracies(
                                         df=test_data,
                                         dep_var=dep_var,
                                         indep_vars=indep_vars,
                                         model=model
                                     )['WMAPE']
                                 ) / 100
    print(iter)
    if type(export_path) == str:
        if iter > 1:
            result_table = pd.concat(
                [
                    temp,
                    result_table
                 ],
                axis=0)
        else:
            None
        with pd.ExcelWriter(
                path=export_path,
                mode='w',
                date_format='YYYY-MM-DD',
                datetime_format='DD-MMM-YYYY'
        ) as writer:
            result_table.to_excel(
                excel_writer=writer,
                index=False,
                sheet_name='Sheet1',
                engine='openpyxl'
            )

    return result_table
