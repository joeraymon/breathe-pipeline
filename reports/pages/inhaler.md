# Inhaler Usage

Weekly rescue inhaler usage since tracking began.
```sql weekly_usage
select * from breathe.inhaler_usage_weekly
```

<LineChart 
    data={weekly_usage}
    x=week_start
    y=weekly_usage_count
    title="Weekly Inhaler Usage"
/>

<DataTable data={weekly_usage}/>