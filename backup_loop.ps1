while ($true) {

    

	$hora = Get-Date -Format "HH:mm"

    

	if ($hora -eq "13:00" -or $hora -eq "21:00") {

		py C:\backup_manager\backup_auto.py
        
		Start-Sleep -Seconds 70
    
	}

    
Start-Sleep -Seconds 20

}