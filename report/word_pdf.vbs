' Update TOC / figure and table lists, save, export PDF, print the page of each Heading 1.
' Usage: cscript //nologo word_pdf.vbs <full path of .docx>
Dim docx, pdf, w, d, t, p
docx = WScript.Arguments(0)
pdf = Left(docx, Len(docx) - 5) & ".pdf"
Set w = CreateObject("Word.Application")
w.Visible = False
w.DisplayAlerts = 0
Set d = w.Documents.Open(docx, False, False, False)
d.Fields.Update
For Each t In d.TablesOfContents
  t.Update
Next
For Each t In d.TablesOfFigures
  t.Update
Next
d.Save
d.ExportAsFixedFormat pdf, 17
WScript.Echo "pages: " & d.ComputeStatistics(2)
For Each p In d.Paragraphs
  If p.OutlineLevel = 1 Then
    WScript.Echo "H1 page " & p.Range.Information(3) & ": " & Replace(p.Range.Text, vbCr, "")
  End If
Next
d.Close False
w.Quit
