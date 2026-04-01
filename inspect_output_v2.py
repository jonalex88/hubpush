import openpyxl
p = r'c:\Vibes\Hubpush\output v2.xlsx'
wb=openpyxl.load_workbook(p,data_only=True)
ws=wb.active
for r in ws.iter_rows(min_row=1,max_row=10,max_col=5,values_only=True):
    print(r)
wb.close()
