Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Application]::EnableVisualStyles()

$form = New-Object System.Windows.Forms.Form
$form.Text = "Drone Wind Field Test System"
$form.Size = New-Object System.Drawing.Size(450, 350)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false

$label = New-Object System.Windows.Forms.Label
$label.Location = New-Object System.Drawing.Point(20, 20)
$label.Size = New-Object System.Drawing.Size(400, 60)
$label.Text = "Startup Menu`n`nPlease select a component to start:"
$label.Font = New-Object System.Drawing.Font("Arial", 12)
$form.Controls.Add($label)

$result = 0

$btn1 = New-Object System.Windows.Forms.Button
$btn1.Location = New-Object System.Drawing.Point(100, 100)
$btn1.Size = New-Object System.Drawing.Size(250, 50)
$btn1.Text = "Desktop Client (Original)"
$btn1.Font = New-Object System.Drawing.Font("Arial", 11)
$btn1.Add_Click({ $result = 1; $form.Close() })
$form.Controls.Add($btn1)

$btn2 = New-Object System.Windows.Forms.Button
$btn2.Location = New-Object System.Drawing.Point(100, 160)
$btn2.Size = New-Object System.Drawing.Size(250, 50)
$btn2.Text = "Integrated System v2.0"
$btn2.Font = New-Object System.Drawing.Font("Arial", 11)
$btn2.Add_Click({ $result = 2; $form.Close() })
$form.Controls.Add($btn2)

$btn3 = New-Object System.Windows.Forms.Button
$btn3.Location = New-Object System.Drawing.Point(100, 220)
$btn3.Size = New-Object System.Drawing.Size(250, 50)
$btn3.Text = "Web Backend Only"
$btn3.Font = New-Object System.Drawing.Font("Arial", 11)
$btn3.Add_Click({ $result = 3; $form.Close() })
$form.Controls.Add($btn3)

$btnCancel = New-Object System.Windows.Forms.Button
$btnCancel.Location = New-Object System.Drawing.Point(100, 280)
$btnCancel.Size = New-Object System.Drawing.Size(250, 35)
$btnCancel.Text = "Cancel"
$btnCancel.Font = New-Object System.Drawing.Font("Arial", 10)
$btnCancel.Add_Click({ $result = 0; $form.Close() })
$form.Controls.Add($btnCancel)

$form.ShowDialog() | Out-Null

exit $result
