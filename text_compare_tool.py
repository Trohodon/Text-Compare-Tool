Option Compare Database

Public dbUserLog As DAO.Database

Private Sub Form_Load()

    Dim EditModeDisabled As Boolean

    'This checks to see if userID is currently logged in to this DB instance and closes application to prevent multiple logins with same user ID
    Dim checkUser As String
    checkUser = Environ("username")

    Dim UserLog As DAO.Recordset
    Set dbUserLog = CurrentDb()
    Set UserLog = dbUserLog.OpenRecordset("tblUserLog", dbOpenDynaset, dbSeeChanges)

    UserLog.MoveLast
    UserLog.MoveFirst

    While Not UserLog.EOF
        If UserLog.Fields("UserID") = checkUser And IsNull(UserLog.Fields("LogOff")) Then
            MsgBox "Your user ID is currently logged in to this Database. Multiple Logins not allowed. Closing Application", , "Multiple Logins Detected"
            Application.Quit
        End If
        UserLog.MoveNext
    Wend

    UserLog.Close
    'End multiple login check

    EditModeDisabled = Not AuthorizedUser(Environ("username")) 'checks User id or password and if DB is opened in Edit Mode
    LogOn (checkUser) 'logs user ID and time stamps log on
    HideTables (EditModeDisabled) 'Hides tables if not in Edit mode. False triggers EditMode

    If Not EditModeDisabled Then
        If MakeBackup() Then
            MsgBox "DB Back Up Created"
        End If
    End If

End Sub


Private Sub Form_Close()

    LogOff (Environ("username")) 'logs user out on usr log table when form closed

End Sub


Public Function LogOn(sUser As String)

    Dim sSQL As String
    'logs user ID and time of logon

    DoCmd.SetWarnings False

    sSQL = "INSERT INTO tblUserLog (UserID) " & _
           "SELECT '" & sUser & "' AS [User];"

    DoCmd.RunSQL sSQL
    DoCmd.SetWarnings True

End Function


Function LogOff(sUser As String)

    Dim sSQL As String

    DoCmd.SetWarnings False

    sSQL = "UPDATE tblUserLog SET tblUserLog.LogOff = Now() " & _
           "WHERE tblUserLog.UserID='" & sUser & "' AND tblUserLog.LogOff Is Null;"

    DoCmd.RunSQL sSQL
    DoCmd.SetWarnings True

End Function


Function AuthorizedUser(sUser As String) As Boolean

    AuthorizedUser = False 'default to return false for authorized user

    Dim UserList(1 To 20) As String 'List of authorized users including Dominion eid and SCANA user name

    UserList(1) = "au4167g"   'Underwood SCANA
    UserList(2) = "joh1375"   'Martin
    UserList(3) = "jeff907"   'Neal Added 8/28/2024
    UserList(4) = "parker9"   'Parker
    UserList(5) = "edwa438"   'Chapman
    UserList(6) = "rob1426"   'Bartley
    UserList(7) = "ej00002"   'Altman
    UserList(8) = "erne013"   'Kersey
    UserList(9) = "bria782"   'Ulmer
    UserList(10) = "andr532"  'Underwood
    UserList(11) = "zohair1"  'Anjum Added 8/28/2024
    UserList(12) = "eala439"  'Altman SCANA
    UserList(13) = "ek43813"  'Kersey SCANA
    UserList(14) = "am46963"  'Morrison SCANA
    UserList(15) = "alex186"  'Morrison
    UserList(16) = "ec46054"  'Chapman SCANA
    UserList(17) = "bu40967"  'Ulmer SCANA
    UserList(18) = "isaak01"  'Fleshman added 5/20/25
    UserList(19) = "greg523"  'Greg Ridlehuber added 10/22/25
    UserList(20) = "ningchl"  'Ningchao Gao added 10/28/25

    Dim i As Integer
    Dim validUser As Boolean

    validUser = False

    For i = 1 To UBound(UserList)
        If UserList(i) = sUser Then
            validUser = True
        End If
    Next

    If validUser = False Then

        If CheckPassword() Then
            MsgBox "Password is confirmed"
        Else
            DoCmd.SetWarnings False
            MsgBox "Your user ID is not authorized to access the Transmission Planning Model Database. Please contact Transmission Planning for access.", , "Unauthorized User ID"
            LogOff (sUser)
            FailedLogin (sUser)
            Application.Quit
        End If

    Else
        'allows authorized user to open in Edit mode
        If MsgBox("Your user ID is confirmed. Would you like to open in Edit Mode?", vbYesNo, "Authorized User ID") = vbYes Then
            AuthorizedUser = True
        End If
    End If

End Function


Function CheckPassword() As Boolean

    Dim check As Boolean
    Dim passwordInput As String 'password input from prompt
    Dim DB_password As String

    DB_password = "Planning" 'DB password set by Transmission Planning change password here

    passwordInput = InputBox("User ID not recognized, please enter password: ")

    If passwordInput = DB_password Then
        CheckPassword = True
    Else
        CheckPassword = False
    End If

End Function


Function HideTables(hide As Boolean)

    Dim tdf As TableDef

    'If not in Edit mode hide tables to prevent data changes
    For Each tdf In CurrentDb.TableDefs

        If Not (tdf.Name Like "MSys*" _
            Or tdf.Name Like "~*" _
            Or tdf.Name Like "tblUserLog" _
            Or tdf.Name Like "DocumentChanges") Then

            If hide = True Then
                tdf.Attributes = dbHiddenObject
            Else
                tdf.Attributes = 0
            End If

        End If

    Next tdf

End Function


Function FailedLogin(sUser As String)

    Dim sSQL As String

    DoCmd.SetWarnings False

    sSQL = "UPDATE tblUserLog SET tblUserLog.FAILED_LOGIN = 'YES' " & _
           "WHERE tblUserLog.UserID='" & sUser & "' AND tblUserLog.LogOff Is Null;"

    DoCmd.RunSQL sSQL
    DoCmd.SetWarnings True

End Function


Function MakeBackup() As Boolean

    Dim Source As String
    Dim Target As String
    Dim a As Integer
    Dim objFSO As Object
    Dim Path As String

    Path = CurrentProject.Path 'get location of current folder
    Source = CurrentDb.Name

    Target = Path & "\" & Format(Now(), "yyyy-MM-dd_hhmm") & "_DatabaseBackup.accdb"

    'create the backup
    Set objFSO = CreateObject("Scripting.FileSystemObject")
    a = objFSO.CopyFile(Source, Target, True)
    Set objFSO = Nothing

    MakeBackup = True

End Function
