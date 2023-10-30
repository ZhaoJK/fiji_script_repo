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
    Dim i As Integer
    
    ' Specify the folder path containing the images
    FolderPath = "H:\D1"
    FolderName = Split(FolderPath, "\")(UBound(Split(FolderPath, "\")))
    
    Set presentation = ActivePresentation
    Set Slide = presentation.Slides.Add(presentation.Slides.Count + 1, Layout:=ppLayoutBlank)
    
    Set textbox = Slide.Shapes.AddTextbox(Orientation:=msoTextOrientationHorizontal, _
        Left:=5, Top:=5, Width:=200, Height:=100)
    textbox.TextFrame.TextRange.Text = "Treatment at " & FolderName
    
    ' Format the text as needed
    textbox.TextFrame.TextRange.Font.Size = 18
    textbox.TextFrame.TextRange.Font.Color.RGB = RGB(0, 0, 255)
    
    ' Loop through each possible combination (A1, A2, A3, ..., D6)
    For i = 1 To 5
        char = Chr(Asc("A") + i - 1) ' Convert 1-4 to A-D
        ColumnNum = i
        For j = 1 To 7
            RowNum = j
            ' Generate the full image path

            FileName = FolderName & "-" & Format(i, "0") & "-" & Format(j, "000") & ".tif"
            ImagePath = FolderPath & "\" & FileName
            
            FileExists = Dir(ImagePath) <> ""
            If FileExists Then
                ' Insert the image on the current slide and set its size
                Set Picture = Slide.Shapes.AddPicture(FileName:=ImagePath, LinkToFile:=msoFalse, _
                    SaveWithDocument:=msoTrue, Left:=120 * (ColumnNum), Top:=90 * (RowNum), Width:=120, Height:=90)
                
                ' Set the image title with the file name
                Picture.Title = FileName
                
                Set textbox = Slide.Shapes.AddTextbox(Orientation:=msoTextOrientationHorizontal, _
                               Left:=120 * (ColumnNum), Top:=90 * (RowNum), Width:=120, Height:=50)
                textbox.TextFrame.TextRange.Text = "Sample_" & i & "_rep_" & j
                textbox.TextFrame.TextRange.Font.Size = 8
                textbox.TextFrame.TextRange.Font.Color.RGB = RGB(255, 255, 255)
                
                Set Group = Slide.Shapes.Range(Array(Picture.Name, textbox.Name)).Group
                Group.Title = FileName
            End If
            
            ' Increment row and column counters
        Next j
    Next i
    
End Sub


