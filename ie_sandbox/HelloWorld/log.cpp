#include "stdafx.h"
#include "resource.h"
#include "HelloWorld_i.h"
#include "dllmain.h"
#include <Windows.h>
#include <iepmapi.h>
#include <iostream>
#include <windows.h>
#include <stdio.h>
#include "broker.h"
#include <RpcDce.h>
#include <KnownFolders.h>
#include "log.h"

TCHAR szTempFile[MAX_PATH] = {0};
BOOL log_created = FALSE;

// Log a string in an available temp file
void writeLog(char *logstr) {
	HRESULT hr;
	LPWSTR pwszSelectedFilename = NULL;
	LPWSTR cacheDir = NULL;
	HANDLE log = NULL;
	DWORD nbytes = 0;

	if(log_created == FALSE) {
		hr = IEGetWriteableFolderPath(FOLDERID_InternetCache, &cacheDir);
		if(!SUCCEEDED(hr)) {
			MessageBox(0, (LPCWSTR)L"No log Available", (LPCWSTR)L"Log error", MB_OK);
			return;
		}

		GetTempFileName(cacheDir, _T("bt_"), 0, szTempFile);
		CoTaskMemFree(cacheDir);
		log_created = TRUE;
	}

	//MessageBox(0, (LPCWSTR)szTempFile, (LPCWSTR)L"okokok", MB_OK);

	log = CreateFile(
		szTempFile,
		FILE_APPEND_DATA,
		0,
		NULL,
		OPEN_EXISTING,
		FILE_ATTRIBUTE_NORMAL,
		NULL);
	
	if(log == INVALID_HANDLE_VALUE) {
		MessageBox(0, (LPCWSTR)L"No log Available", (LPCWSTR)L"Log error", MB_OK);
		return;
	}
	
	BOOL a = WriteFile(
		log,
		logstr,
		(DWORD)strlen(logstr),
		&nbytes,
		NULL);

	CloseHandle(log);

	if(a == FALSE)
		MessageBox(0, (LPCWSTR)L"Write error!", (LPCWSTR)L"Log error", MB_OK);

}


