' Opens the budget workbook in Excel (read-only), recalculates, prints Summary B8:B15. Usage: cscript //nologo xlsx_totals.vbs <xlsx>
Dim xl, wb, ws, r
Set xl = CreateObject("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
Set wb = xl.Workbooks.Open(WScript.Arguments(0), 0, True)
xl.CalculateFull
Set ws = wb.Worksheets("Summary")
For r = 8 To 15
  WScript.Echo ws.Cells(r, 1).Text & " | " & FormatNumber(ws.Cells(r, 2).Value, 2)
Next
wb.Close False
xl.Quit
