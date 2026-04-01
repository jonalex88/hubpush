import openpyxl
p = r'c:\Vibes\Hubpush\outputv1.xlsx'
wb=openpyxl.load_workbook(p,data_only=True)
ws=wb.active
for r in ws.iter_rows(min_row=1,max_row=12,max_col=4,values_only=True):
    print(r)
wb.close()
