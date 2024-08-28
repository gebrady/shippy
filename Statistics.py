import matplotlib as plt


class Statistics():

    def __init__(self, boatsData):
        self.boatsData = boatsData

    def histogram(self, data, field):
        pass

        
    def grouped_table(self, data, field):
        pass

    def summary_stats(self, data, group_field, stats_field):
        pass
    
    @staticmethod
    def summary_table(boatsData, group_field : str, stats_fields : list, stats_type : list):
        agg_dict = {field: stats_type for field in stats_fields}
        stats = boatsData.flatten().groupby(group_field).agg(agg_dict).reset_index()

        stats.columns = ['_'.join(col).strip() if col[1] else col[0] for col in stats.columns]
        stats.rename(columns={f'{group_field}_': f'{group_field}'}, inplace=True)
        return stats