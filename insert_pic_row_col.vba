Sub ArrangeImagesByPattern()

'author: jiakuan.zhao
'date: 20231030
'Fucniont:
'add new slides in current ppt
'input images from folder
'image title like D1-1-001

    Dim SlideNum As Integer
    Dim RowNum As Integer
    Dim ColumnNum As Integer
    Dim FolderPath, FolderName As String
    Dim FileName As String
    Dim ImagePath As String
    Dim presentation As presentation
    Dim Slide As Slide
    Dim Picture As Shape
    Dim char As String
    Dim sample_id As Integer
    
    'sample from 1-5
    sample_id = 3
    FolderPath = "H:\Exp_stuff\human-fascia-jiakuan\"
    'FolderName = Split(FolderPath, "\")(UBound(Split(FolderPath, "\")))
    
    Set presentation = ActivePresentation
    Set Slide = presentation.Slides.Add(presentation.Slides.Count + 1, Layout:=ppLayoutBlank)
    
    Set textbox = Slide.Shapes.AddTextbox(Orientation:=msoTextOrientationHorizontal, _
        Left:=5, Top:=5, Width:=200, Height:=100)
    textbox.TextFrame.TextRange.Text = "Sample_" & sample_id
    
    
    ' Format the text as needed
    textbox.TextFrame.TextRange.Font.Size = 18
    textbox.TextFrame.TextRange.Font.Color.RGB = RGB(0, 0, 255)
    
    ' Loop through days from 0 to 10
    For i = 0 To 10 Step 2
        char = Chr(Asc("A") + i - 1) ' Convert 1-4 to A-D
        ColumnNum = (i + 2) / 2
        For j = 1 To 7
            RowNum = j
            ' Generate the full image path
            
            ImagePath = FolderPath & "D" & i & "\D" & i & "-" & sample_id & "-" & Format(j, "000") & ".tif"
            
            FileExists = Dir(ImagePath) <> ""
            If FileExists Then
                ' Insert the image on the current slide and set its size
                Set Picture = Slide.Shapes.AddPicture(FileName:=ImagePath, LinkToFile:=msoFalse, _
                    SaveWithDocument:=msoTrue, Left:=120 * (ColumnNum), Top:=90 * (RowNum), Width:=120, Height:=90)
                
                ' Set the image title with the file name
                Picture.Title = FileName
                
                Set textbox = Slide.Shapes.AddTextbox(Orientation:=msoTextOrientationHorizontal, _
                               Left:=120 * (ColumnNum), Top:=90 * (RowNum), Width:=120, Height:=50)
                textbox.TextFrame.TextRange.Text = "D" & i & "_Sample_" & sample_id & "_rep_" & j
                textbox.TextFrame.TextRange.Font.Size = 8
                textbox.TextFrame.TextRange.Font.Color.RGB = RGB(255, 255, 255)
                
                Set Group = Slide.Shapes.Range(Array(Picture.Name, textbox.Name)).Group
                Group.Title = FileName
            End If
            
            ' Increment row and column counters
        Next j
    Next i
    
End Sub





