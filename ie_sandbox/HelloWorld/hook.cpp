#include "stdafx.h"
#include "resource.h"
#include "HelloWorld_i.h"
#include "dllmain.h"
#include <Windows.h>
#include "hook.h"
#include "log.h"


BOOL install_hook(void) {
	HINSTANCE dllHandle = NULL;
	writeLog("[*] Installing hook....\r\n");
	writeLog("[*] Looking for ole32.dll\r\n");

	dllHandle = LoadLibrary((LPCWSTR)L"ole32.dll");
	// Get an handle to the iertutil.dll library
	if(dllHandle != NULL)
		writeLog("[+] ole32.dll correctly imported!\r\n");
	else {
		writeLog("[-] Unable to find iertutil.dll... aborting!\r\n");
		return NULL;
	}

	writeLog("[*] Looking for  method\r\n");
	// Get the entry point for the CoCreateUserBroker method (exported as #58 entry)
	int (*NdrStubCall2_ptr)(void *, void *, void *, void *) =  (int (*)(void *, void *, void *, void *)) GetProcAddress(dllHandle, (LPCSTR)"NdrStubCall2");

	if(NdrStubCall2_ptr != NULL) 
		writeLog("[+] Method CoCreateUserBroker correctly found!\r\n");
	else {
		writeLog("[-] Unable to find CoCreateUserBroker method.... aborting!\r\n");
		return NULL;
	}

	// Return the IEUserBroker object
	return true;
}