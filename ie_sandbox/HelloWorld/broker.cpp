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
#include "log.h"

extern unsigned long ESP_RESTORE;


// CoCreateUser function in ieframe.dll.
// We use it to get the IEUserBroker interface
int (*coCreateUserBroker)(IE_USER_BROKER_OBJ*);

/************************************/
/**** GUID FOR INTERFACES WE NEED ***/
/************************************/

struct _GUID CLSID_CProtectedModeAPINoFrameAffinity = {0x8C537469, 0x1EA9, 0x4C85, {0x99, 0x47, 0x7e, 0x41, 0x85, 0, 0xcd, 0xd4}};
struct _GUID IID_ProtectedModeAPI =                   {0x3853EAB3, 0xadb3, 0x4be8, {0x9c, 0x96, 0xc8, 0x83, 0xb9, 0x8e, 0x76, 0xad}};
struct _GUID CLSID_CShdocvwBroker =                   {0x9C7A1728, 0xb694, 0x427a, {0x94, 0xa2, 0xa1, 0xb2, 0xc6, 0xf, 0x3, 0x60}};
struct _GUID CLSID_CShdocvwBrokerNoFrame =            {0x20CCEF1E, 0x185,  0x41A5, {0xa9, 0x33, 0x50, 0x9c, 0x43, 0xb5, 0x4f, 0x98}};
struct _GUID GUID_Get_CshdocvwBroker =                {0x151B1F5F, 0x25cd, 0x45f9, {0xad, 0xbc, 0xb8, 0x5a, 0x66, 0xbf, 0xb6, 0x8b}};
struct _GUID CLSID_IERecoveryStore =                  {0x10BCEB99, 0xFAAC, 0x4080, {0xb2, 0xfa, 0xd0, 0x7c, 0xd6, 0x71, 0xee, 0xf2}};
struct _GUID GUID_Get_IERecoveryStore =               {0xCBEBAD9C, 0x452A, 0x43cb, {0x80, 0x37, 0x44, 0x1e, 0xa7, 0x74, 0x62, 0x3e}}; 
struct _GUID CLSID_IERegHelperBroker =                {0x41DC24D8, 0x6B81, 0x41C4, {0x83, 0x2c, 0xfe, 0x17, 0x2c, 0xb3, 0xa5, 0x82}};
struct _GUID CLSID_IERegHelperBrokerCleanup =         {0xC40B45C3, 0x1518, 0x46FB, {0xa0, 0xf0, 0xc,  0x5,  0x61, 0x74, 0xd5, 0x55}};
struct _GUID CLSID_IEAxInstallBrokerBroker =          {0xC6BAE7E5, 0xC740, 0x4996, {0xb9, 0xc9, 0xad, 0x4d, 0x3a, 0x68, 0x98, 0xd1}};
struct _GUID CLSID_IEBrokerAttach =                   {0x7673B35E, 0x907A, 0x449D, {0xa4, 0x9f, 0xe5, 0xce, 0x47, 0xf0, 0xb0, 0xb2}};
struct _GUID CLSID_CIeAxiInstaller =                  {0xBDB57FF2, 0x79B9, 0x4205, {0x94, 0x47, 0xf5, 0xfe, 0x85, 0xf3, 0x73, 0x12}};
struct _GUID CLSID_CSettingsBroker =                  {0xC6CC0D21, 0x895d, 0x49cc, {0x98, 0xf1, 0xd2, 0x8, 0xcd, 0x71, 0xe0, 0x47}};
struct _GUID GUID_Get_CSettingsBroker =               {0xEA77E0BC, 0x3ce7, 0x4cc1, {0x92, 0x8f, 0x6f, 0x50, 0xa0, 0xce, 0x54, 0x87}};
struct _GUID CLSID_FeedsLoriBroker =                  {0xA7C922A0, 0xA197, 0x4AE4, {0x8F, 0xCD, 0x22, 0x36, 0xBB, 0x4C, 0xF5, 0x15}};
struct _GUID GUID_FeedsLoriBroker2 =                  {0x7AB1E58, 0x91A0, 0x450F, {0xb4, 0xa5, 0xa4, 0xc7, 0x75, 0xe6, 0x73, 0x59}};
struct _GUID CLSID_FeedsArbiterLoriBroker =           {0x34e6abfe, 0xe9f4, 0x4ddf, {0x89, 0x5a, 0x73, 0x50, 0xe1, 0x98, 0xf2, 0x6e}};
struct _GUID GUID_FeedsArbiterLoriBroker2 =           {0xedb9ef13, 0x45c, 0x4c0a,  {0x80, 0x8e, 0x32, 0x94, 0xc5, 0x97, 0x3, 0xb4}};  
struct _GUID IID_ShellWindow =                        {0x85CB6900, 0x4D95, 0x11CF, {0x96, 0xc, 0, 0x80, 0xc7, 0xf4, 0xee, 0x85}};

struct _GUID IID_ItabWindow = {0x54862BD, 0x0E602, 0x4DBC, {0x8f, 0x91, 0xc0, 0x6, 0x45, 0x1a, 0x82, 2}};

IE_USER_BROKER_OBJ *iebroker_iface = NULL;
STD_IDENTITY_OBJ *identity_iface = NULL;
PROTECTED_MODE_OBJ *protected_iface = NULL;
SH_BROKER_OBJ *shbroker_iface = NULL;
IERECOVERY_STORE_OBJ *recoveryStore_iface = NULL;
SETTINGSSTORE_OBJ *settingsStore_iface = NULL;
IEREGHELPER_BROKER_OBJ *ieRegHelperBroker_iface = NULL;
IEREGHELPER_CLEANUP_OBJ *ieRegHelperCleanup_iface = NULL;
IEBROKERATTACH_OBJ* ieBrokerAttach_iface = NULL;
IEAXINSTALLBROKER_OBJ *ieAxInstallBroker_iface = NULL;
FEEDSARBITERLORI_BROKER_OBJ *FeedsArbiterLoriBroker_iface = NULL;
FEEDSLORI_BROKER_OBJ *FeedsLoriBroker_iface = NULL;
SHELLWINDOW_OBJ *ShellWindow_iface = NULL;

#define PROLOGUE {\
		__asm push ebp\
		__asm mov ebp, esp\
	    }


#define EPILOGUE {\
		__asm mov esp, ebp \
		__asm pop ebp \
		__asm ret\
	    }




/********* IEUserBroker Interface *******/
/****************************************/

IE_USER_BROKER_OBJ* getUserBrokerInterface() {	
	HINSTANCE dllHandle = NULL;
	IE_USER_BROKER_OBJ *broker_ptr = NULL;

	writeLog("[*] Looking for iertutil.dll\r\n");

	dllHandle = LoadLibrary((LPCWSTR)L"iertutil.dll");
	// Get an handle to the iertutil.dll library
	if(dllHandle != NULL)
		writeLog("[+] iertutil.dll correctly imported!\r\n");
	else {
		writeLog("[-] Unable to find iertutil.dll... aborting!\r\n");
		return NULL;
	}

	writeLog("[*] Looking for CoCreateUserBroker method\r\n");
	// Get the entry point for the CoCreateUserBroker method (exported as #58 entry)
	int (*coCreateUserBroker)(void *) =  (int (*)(void *)) GetProcAddress(dllHandle, (LPCSTR) COCREATEUSERBROKER_ENTRY);

	if(coCreateUserBroker != NULL) 
		writeLog("[+] Method CoCreateUserBroker correctly found!\r\n");
	else {
		writeLog("[-] Unable to find CoCreateUserBroker method.... aborting!\r\n");
		return NULL;
	}

	// Return the IEUserBroker object
	coCreateUserBroker(&broker_ptr);
	return broker_ptr;
}



/*********************************************/
/* Get an interface from the broker **********/
/*********************************************/

// For some reason the calling convention for the broker functions is different in visual studio.
// For these reason we use naked function writing prologue and epilogue by hand to be sure that the 
// stack pointer will be correct before to return.



/****** ProtectedModeAPI Interface ***********/
/*********************************************/

PROTECTED_MODE_OBJ* getProtectedModeAPIInterface() { 

	if(protected_iface == NULL) {
		iebroker_iface = getUserBrokerInterface();

		if(iebroker_iface == NULL) {
			writeLog("[-] ProtectedModeAPI: Unable to retrieve IEUserBroker object... aborting\r\n");
			return NULL;
		}

		writeLog("[*] ProtectedModeAPI: Initializing broker object\r\n");
		IEUserBroker_Initialize(iebroker_iface, 0, 0, NULL);
		writeLog("[*] ProtectedModeAPI: Getting StdIdentity object\r\n");
		IEUserBroker_CreateKnownObject(iebroker_iface, &CLSID_CProtectedModeAPINoFrameAffinity, (GUID *)&IID_IUnknown, &identity_iface);

		if(identity_iface == NULL) {
			writeLog("[-] ProtectedModeAPI: Unable to retrieve StdIdentity object... aborting\r\n");
			return NULL;
		}

		writeLog("[+] ProtectedModeAPI: StdIdentity object correctly retrieved\r\n");
		writeLog("[*] ProtectedModeAPI: Getting ProtectedModeAPI object\r\n");
		CStdIdentity_QueryInterfaces(identity_iface, &IID_ProtectedModeAPI, (void **)&protected_iface);
	}

	if(protected_iface == NULL) 
		writeLog("[-] ProtectedModeAPI: Unable to retrieve ProtectedModeAPI object... aborting\r\n");
	else
		writeLog("[+] ProtectedModeAPI: ProtectedModeAPI object correctly retrieved\r\n");

	return protected_iface;
}


/******* ShDocvwBroker Interface *****************/
/*************************************************/

SH_BROKER_OBJ* getShBrokerIface() { 

	if(shbroker_iface == NULL) {
		iebroker_iface = getUserBrokerInterface();
	    
		if(iebroker_iface == NULL) {
			writeLog("[-] ShDocvwBroker: Unable to retrieve IEUserBroker object... aborting\r\n");
			return NULL;
		}

		writeLog("[*] ShDocvwBroker: Initializing broker object\r\n");
		IEUserBroker_Initialize(iebroker_iface, 0, 0, NULL);
		writeLog("[*] ShDocvwBroker: Getting StdIdentity object\r\n");
		IEUserBroker_CreateKnownObject(iebroker_iface, &CLSID_CShdocvwBroker, (GUID *)&IID_IUnknown, &identity_iface);
		
		if(identity_iface == NULL) {
			writeLog("[-] ShDocvwBroker: Unable to retrieve StdIdentity object... aborting\r\n");
			return NULL;
		}
		
		writeLog("[+] ShDocvwBroker: StdIdentity object correctly retrieved\r\n");
		writeLog("[*] ShDocvwBroker: Getting ShDocvwBrokerObj object\r\n");
		CStdIdentity_QueryInterfaces(identity_iface, &GUID_Get_CshdocvwBroker, (void **)&shbroker_iface);
	}

	if(shbroker_iface == NULL) 
		writeLog("[-] ShDocvwBroker: Unable to retrieve ShDocvwBroker object... aborting\r\n");
	else
		writeLog("[+] ShDocvwBroker: ShDocvwBroker object correctly retrieved\r\n");

	return shbroker_iface;
}




/******* IERecoveryStore Interface *****************/
/*************************************************/

IERECOVERY_STORE_OBJ* getRecoveryStoreIface() { 

	if(recoveryStore_iface == NULL) {
		iebroker_iface = getUserBrokerInterface();
	    
		if(iebroker_iface == NULL) {
			writeLog("[-] IERecoveryStore: Unable to retrieve IEUserBroker object... aborting\r\n");
			return NULL;
		}

		writeLog("[*] IERecoveryStore: Initializing broker object\r\n");
		IEUserBroker_Initialize(iebroker_iface, 0, 0, NULL);
		writeLog("[*] IERecoveryStore: Getting StdIdentity object\r\n");
		IEUserBroker_CreateKnownObject(iebroker_iface, &CLSID_IERecoveryStore, (GUID *)&IID_IUnknown, &identity_iface);
		
		if(identity_iface == NULL) {
			writeLog("[-] IERecoveryStore: Unable to retrieve StdIdentity object... aborting\r\n");
			return NULL;
		}
		
		writeLog("[+] IERecoveryStore: StdIdentity object correctly retrieved\r\n");
		writeLog("[*] IERecoveryStore: Getting IERecoveryStore object\r\n");
		CStdIdentity_QueryInterfaces(identity_iface, &GUID_Get_IERecoveryStore, (void **)&recoveryStore_iface);
	}

	if(recoveryStore_iface == NULL) 
		writeLog("[-] IERecoveryStore: Unable to retrieve IERecoveryStore object... aborting\r\n");
	else
		writeLog("[+] IERecoveryStore: IERecoveryStore object correctly retrieved\r\n");

	return recoveryStore_iface;
}



/******* SettingsStore Interface *****************/
/*************************************************/
SETTINGSSTORE_OBJ* getSettingsStoreIface() { 
	
	if(settingsStore_iface == NULL) {
		iebroker_iface = getUserBrokerInterface();
	    
		if(iebroker_iface == NULL) {
			writeLog("[-] SettingsStore: Unable to retrieve IEUserBroker object... aborting\r\n");
			return NULL;
		}

		writeLog("[*] SettingsStore: Initializing broker object\r\n");
		IEUserBroker_Initialize(iebroker_iface, 0, 0, NULL);
		writeLog("[*] SettingsStore: Getting StdIdentity object\r\n");
		IEUserBroker_CreateKnownObject(iebroker_iface, &CLSID_CSettingsBroker, (GUID *)&IID_IUnknown, &identity_iface);
		
		if(identity_iface == NULL) {
			writeLog("[-] SettingsStore: Unable to retrieve StdIdentity object... aborting\r\n");
			return NULL;
		}
		
		writeLog("[+] SettingsStore: StdIdentity object correctly retrieved\r\n");
		writeLog("[*] SettingsStore: Getting SettingsStore object\r\n");
		CStdIdentity_QueryInterfaces(identity_iface, &GUID_Get_CSettingsBroker, (void **)&settingsStore_iface);
	}

	if(settingsStore_iface == NULL) 
		writeLog("[-] SettingsStore: Unable to retrieve SettingsStore object... aborting\r\n");
	else
		writeLog("[+] SettingsStore: SettingsStore object correctly retrieved\r\n");

	return settingsStore_iface;
}


/******* IERegHelperBroker Interface *****************/
/*************************************************/
IEREGHELPER_BROKER_OBJ* getIERegHelperBrokerIface() {
	iebroker_iface = getUserBrokerInterface();
	    
	if(iebroker_iface == NULL) {
		writeLog("[-] IERegHelperBroker: Unable to retrieve IEUserBroker object... aborting\r\n");
		return NULL;
	}

	writeLog("[*] IERegHelperBroker: Initializing broker object\r\n");
	IEUserBroker_Initialize(iebroker_iface, 0, 0, NULL);
	writeLog("[*] IERegHelperBroker: Getting IERegHelperBroker object\r\n");
	IEUserBroker_QueryInterface(iebroker_iface, &CLSID_IERegHelperBroker, &ieRegHelperBroker_iface);

	if(ieRegHelperBroker_iface == NULL) 
		writeLog("[-] IERegHelperBroker: Unable to retrieve IERegHelperBroker object... aborting\r\n");
	else
		writeLog("[+] IERegHelperBroker: IERegHelperBroker object correctly retrieved\r\n");

	return ieRegHelperBroker_iface;
}



/******* IERegHelperCleanup Interface *****************/
/*************************************************/
IEREGHELPER_CLEANUP_OBJ* getIERegHelperCleanupIface() {
	iebroker_iface = getUserBrokerInterface();
	    
	if(iebroker_iface == NULL) {
		writeLog("[-] IERegHelperCleanup: Unable to retrieve IEUserBroker object... aborting\r\n");
		return NULL;
	}

	writeLog("[*] IERegHelperCleanup: Initializing broker object\r\n");
	IEUserBroker_Initialize(iebroker_iface, 0, 0, NULL);
	writeLog("[*] IERegHelperCleanup: Getting IERegHelperCleanup object\r\n");
	IEUserBroker_QueryInterface(iebroker_iface, &CLSID_IERegHelperBrokerCleanup, &ieRegHelperCleanup_iface);

	if(ieRegHelperCleanup_iface == NULL) 
		writeLog("[-] IERegHelperCleanup: Unable to retrieve IERegHelperCleanup object... aborting\r\n");
	else
		writeLog("[+] IERegHelperCleanup: IERegHelperCleanup object correctly retrieved\r\n");

	return ieRegHelperCleanup_iface;
}



/******* IEBrokerAttach Interface *****************/
/*************************************************/
IEBROKERATTACH_OBJ* getIEBrokerAttachIface() {
	iebroker_iface = getUserBrokerInterface();
	    
	if(iebroker_iface == NULL) {
		writeLog("[-] IEBrokerAttach: Unable to retrieve IEUserBroker object... aborting\r\n");
		return NULL;
	}

	writeLog("[*] IEBrokerAttach: Initializing broker object\r\n");
	IEUserBroker_Initialize(iebroker_iface, 0, 0, NULL);
	writeLog("[*] IEBrokerAttach: Getting IEBrokerAttach object\r\n");
	IEUserBroker_QueryInterface(iebroker_iface, &CLSID_IEBrokerAttach, &ieBrokerAttach_iface);

	if(ieBrokerAttach_iface == NULL) 
		writeLog("[-] IEBrokerAttach: Unable to retrieve IEBrokerAttach object... aborting\r\n");
	else
		writeLog("[+] IEBrokerAttach: IEBrokerAttach object correctly retrieved\r\n");

	return ieBrokerAttach_iface;
}


/******* IEAxInstallBroker Interface *****************/
/*****************************************************/
IEAXINSTALLBROKER_OBJ* getIEAxInstallBrokerIface() {
	iebroker_iface = getUserBrokerInterface();
	    
	if(iebroker_iface == NULL) {
		writeLog("[-] IEAxInstallBroker: Unable to retrieve IEUserBroker object... aborting\r\n");
		return NULL;
	}

	writeLog("[*] IEAxInstallBroker: Initializing broker object\r\n");
	IEUserBroker_Initialize(iebroker_iface, 0, 0, NULL);
	writeLog("[*] IEAxInstallBroker: Getting IEAxInstallBroker object\r\n");
	IEUserBroker_QueryInterface(iebroker_iface, &CLSID_IEAxInstallBrokerBroker, &ieAxInstallBroker_iface);

	if(ieAxInstallBroker_iface == NULL) 
		writeLog("[-] IEAxInstallBroker: Unable to retrieve IEAxInstallBroker object... aborting\r\n");
	else
		writeLog("[+] IEAxInstallBroker: IEAxInstallBroker object correctly retrieved\r\n");

	return ieAxInstallBroker_iface;
}


/******* FeedsArbiterLoriBroker Interface *****************/
/*****************************************************/
FEEDSARBITERLORI_BROKER_OBJ* getFeedsArbiterLoriBrokerIface() {
	if(FeedsArbiterLoriBroker_iface == NULL) {
		iebroker_iface = getUserBrokerInterface();
	    
		if(iebroker_iface == NULL) {
			writeLog("[-] FeedsArbiterLoriBroker: Unable to retrieve IEUserBroker object... aborting\r\n");
			return NULL;
		}

		writeLog("[*] FeedsArbiterLoriBroker: Initializing broker object\r\n");
		IEUserBroker_Initialize(iebroker_iface, 0, 0, NULL);
		writeLog("[*] FeedsArbiterLoriBroker: Getting StdIdentity object\r\n");
		IEUserBroker_CreateKnownObject(iebroker_iface, &CLSID_FeedsArbiterLoriBroker, (GUID *)&GUID_FeedsArbiterLoriBroker2, &FeedsArbiterLoriBroker_iface);
		
		if(FeedsArbiterLoriBroker_iface == NULL) {
			writeLog("[-] FeedsArbiterLoriBroker: Unable to retrieve FeedsArbiterLoriBroker object... aborting\r\n");
			return NULL;
		}
		
		writeLog("[+] FeedsArbiterLoriBroker: FeedsArbiterLoriBroker object correctly retrieved\r\n");
	}
	return FeedsArbiterLoriBroker_iface;
}



/******* FeedsLoriBroker Interface *****************/
/*****************************************************/
FEEDSLORI_BROKER_OBJ* getFeedsLoriBrokerIface() {
	if(FeedsLoriBroker_iface == NULL) {
		iebroker_iface = getUserBrokerInterface();
	    
		if(iebroker_iface == NULL) {
			writeLog("[-] FeedsLoriBroker: Unable to retrieve IEUserBroker object... aborting\r\n");
			return NULL;
		}

		writeLog("[*] FeedsLoriBroker: Initializing broker object\r\n");
		IEUserBroker_Initialize(iebroker_iface, 0, 0, NULL);
		writeLog("[*] FeedsLoriBroker: Getting StdIdentity object\r\n");
		IEUserBroker_CreateKnownObject(iebroker_iface, &CLSID_FeedsLoriBroker, (GUID *)&GUID_FeedsLoriBroker2, &FeedsLoriBroker_iface);
		
		if(FeedsLoriBroker_iface == NULL) {
			writeLog("[-] FeedsLoriBroker: Unable to retrieve FeedsLoriBroker_iface object... aborting\r\n");
			return NULL;
		}
		
		writeLog("[+] FeedsLoriBroker: FeedsLoriBroker_iface object correctly retrieved\r\n");
	}

	return FeedsLoriBroker_iface;
}



/******* ShellWindow Interface *****************/
/*****************************************************/
SHELLWINDOW_OBJ* getShellWindowIface() {
	IUnknown *unk = NULL;

	SH_BROKER_OBJ *shbroker = getShBrokerIface();
	if(shbroker == NULL) {
		writeLog("[+] ShellWindow: Unable to retrieve ShDocvwBroker object... aborting\r\n");
		return NULL;
	}

	if(ShellWindow_iface != NULL)
		return ShellWindow_iface;

	shbroker->iface->GetShellWindows((HANDLE)shbroker, &unk);
	if(unk == NULL) {
		writeLog("[+] ShellWindow: Unable to retrieve ShDocvwBroker object... aborting\r\n");
		return NULL;
	}

	STD_IDENTITY_OBJ *g = (STD_IDENTITY_OBJ *) unk;
	CStdIdentity_QueryInterfaces(g, &IID_ShellWindow, (void **)&ShellWindow_iface);
	//CStdIdentity_QueryInterfaces(g, &IID_ItabWindow, (void **)&ShellWindow_iface);
	

	if(ShellWindow_iface == NULL) {
			writeLog("[-] ShellWindow: Unable to retrieve ShellWindow_iface object... aborting\r\n");
			return NULL;
	}
		
	writeLog("[+] ShellWindow: ShellWindow_iface object correctly retrieved\r\n");
	return ShellWindow_iface;

}


/**********************************************/
/******* BROKER CALL WRAPPERS *****************/
/**********************************************/


// For some reason the calling convention for the broker functions is different in visual studio.
// For these reason we use naked function writing prologue and epilogue by hand to be sure that the 
// stack pointer will be correct before to return.


/*****************************/
/**** IEUserBroker object ****/
/*****************************/

__declspec(naked) void IEUserBroker_Initialize(IE_USER_BROKER_OBJ *iebroker, long a, long b, void *c) {

	PROLOGUE

	iebroker->iface->initialize((HANDLE)iebroker, a, b, c);

	EPILOGUE
}


__declspec(naked) void IEUserBroker_QueryInterface(IE_USER_BROKER_OBJ *iebroker, struct _GUID *a, void *b) {

	PROLOGUE

	iebroker->iface->queryInterface((HANDLE)iebroker, a, b);

	EPILOGUE

}


__declspec(naked) void IEUserBroker_CreateKnownObject(IE_USER_BROKER_OBJ *iebroker, struct _GUID *guid1, struct _GUID *guid2, void* identity) {

	PROLOGUE

	iebroker->iface->createKnownObject((HANDLE)iebroker, guid1, guid2, identity);

	EPILOGUE

}


/*****************************/
/**** StdIdentity object *****/
/*****************************/


__declspec(naked) void CStdIdentity_QueryInterfaces(STD_IDENTITY_OBJ *identity, struct _GUID *guid, void **container) {

	PROLOGUE

	identity->iface->QueryInterface((HANDLE)identity, guid, container);

	EPILOGUE
}


__declspec(naked) void CStdIdentity_QueryInternalInterface(STD_IDENTITY_OBJ *identity, struct _GUID *guid, void **container) {
	PROLOGUE

	identity->iface->QueryInternalInterface((HANDLE)identity, guid, container);

	EPILOGUE
}



/*********************************/
/**** ProtectedModeAPI object ****/
/*********************************/


__declspec(naked) void ProtectedModeAPI_QueryInterface(PROTECTED_MODE_OBJ *protectedmode, struct _GUID *guid, void **container) {
	PROLOGUE

	protectedmode->iface->QueryInterface((HANDLE)protectedmode, guid, container);

	EPILOGUE
}


__declspec(naked) void ProtectedModeAPI_ShowDialog(PROTECTED_MODE_OBJ *protected_mode_api, HANDLE a, LPWSTR b, LPWSTR c, LPCWSTR d, LPCWSTR e, DWORD f, DWORD g, LPWSTR *h) {

	PROLOGUE

	protected_mode_api->iface->ShowSaveFileDialog ((HANDLE)protected_mode_api, a, b, c, d, e, f, g, h);

	EPILOGUE
}


/******************************/
/**** ShdocvwBroker object ****/
/******************************/

__declspec(naked) void ShBroker_QueryInterface(SH_BROKER_OBJ *shbroker, struct _GUID *guid, void **container) {

	PROLOGUE

	shbroker->iface->QueryInterface((HANDLE)shbroker, guid, container);

	EPILOGUE
}


__declspec(naked) void ShBroker_ShowLang(SH_BROKER_OBJ *shbroker, HANDLE a) {

	PROLOGUE

	shbroker->iface->ShowInternetOptionsLanguages((HANDLE)shbroker, a);

	EPILOGUE

}


/********************************/
/**** IESettingsStore object ****/
/********************************/

__declspec(naked) void SettingsStore_QueryInterface(SETTINGSSTORE_OBJ *settings_obj, struct _GUID *guid, void **container) {
	PROLOGUE

	settings_obj->iface->QueryInterface((HANDLE)settings_obj, guid, container);

	EPILOGUE
}

__declspec(naked) void SettingsStore_DeleteValue(SETTINGSSTORE_OBJ *settings_obj, _GUID *a, int b) {
	PROLOGUE

	settings_obj->iface->DeleteValue((HANDLE)settings_obj, &CLSID_CSettingsBroker, b);

	EPILOGUE
}

/********************************/
/**** IERecoveryStore object ****/
/********************************/

__declspec(naked) void IERecoveryStore_QueryInterface(IERECOVERY_STORE_OBJ *recovery_store, struct _GUID *guid, void **container) {
	PROLOGUE

	recovery_store->iface->QueryInterface((HANDLE)recovery_store, guid, container);

	EPILOGUE
}

__declspec(naked) void IERecoveryStore_Shutdown(IERECOVERY_STORE_OBJ *recovery_store) {

	PROLOGUE

	recovery_store->iface->Shutdown(recovery_store);

	EPILOGUE
}



/********************************/
/**** IERegHelperBroker object ****/
/********************************/

__declspec(naked) void IERegHelperBroker_QueryInterface(IEREGHELPER_BROKER_OBJ *regbroker, struct _GUID *guid, void **container) {
	PROLOGUE

	regbroker->iface->QueryInterface_ad4((HANDLE)regbroker, guid, container);

	EPILOGUE
}



__declspec(naked) void IERegHelperBroker_DoCreateKey(IEREGHELPER_BROKER_OBJ *regbroker, int a) {

	PROLOGUE

	regbroker->iface->DoCreateKey((HANDLE) regbroker, a);

	EPILOGUE
}


/********************************/
/**** IERegHelperCleanup object ****/
/********************************/

__declspec(naked) void IERegHelperCleanup_QueryInterface(IEREGHELPER_CLEANUP_OBJ *regcleanup, struct _GUID *guid, void **container) {
	PROLOGUE

	regcleanup->iface->QueryInterface_ad8((HANDLE)regcleanup, guid, container);

	EPILOGUE
}

__declspec(naked) void IERegHelperCleanup_RegisterCleanup(IEREGHELPER_CLEANUP_OBJ *regcleanup, IUnknown *a) {
	PROLOGUE

	regcleanup->iface->RegisterCleanup((HANDLE)regcleanup, a);

	EPILOGUE
}


/********************************/
/**** IEBrokerAttach object ****/
/********************************/

__declspec(naked) void IEBrokerAttach_QueryInterface(IEBROKERATTACH_OBJ *brokerAttach, struct _GUID *guid, void **container) {
	PROLOGUE

	brokerAttach->iface->QueryInterface_ad16((HANDLE)brokerAttach, guid, container);

	EPILOGUE
}

__declspec(naked) void IEBrokerAttach_AttachIEFrameToBroker(IEBROKERATTACH_OBJ* brokerAttach, IUnknown *a) {
	PROLOGUE

	brokerAttach->iface->AttachIEFrameToBroker((HANDLE)brokerAttach, a);

	PROLOGUE
}

/***********************************/
/**** IEAxInstallBroker object ****/
/**********************************/
__declspec(naked) void IEAxInstallBroker_QueryInterface(IEAXINSTALLBROKER_OBJ *axinstall_broker, struct _GUID *guid, void **container) {
	PROLOGUE

	axinstall_broker->iface->QueryInterface_ad12((HANDLE)axinstall_broker, guid, container);

	EPILOGUE
}

__declspec(naked) void IEAxInstallBroker_GetAxInstallBroker(IEAXINSTALLBROKER_OBJ *axinstall_broker, HWND *win, IUnknown **e) {

	PROLOGUE

	axinstall_broker->iface->BrokerGetAxInstallBroker((HANDLE)axinstall_broker, &CLSID_CIeAxiInstaller, (GUID *)&IID_IUnknown, NULL, 1, e);

	EPILOGUE
}


/***********************************/
/**** FeedsLoriBroker object ****/
/**********************************/

__declspec(naked) void FeedsLori_QueryInterface(FEEDSLORI_BROKER_OBJ *feedslori, struct _GUID *guid, void **container) {

	PROLOGUE

	feedslori->iface->m0((HANDLE)feedslori, guid, container);

	EPILOGUE
}

/***********************************/
/**** FeedsArbiretLoriBroker object ****/
/**********************************/

__declspec(naked) void FeedsArbiterLori_QueryInterface(FEEDSARBITERLORI_BROKER_OBJ *feedsarbiterlori, struct _GUID *guid, void **container){


	PROLOGUE

	feedsarbiterlori->iface->m0((HANDLE)feedsarbiterlori, guid, container);

	EPILOGUE
}

/***********************************/
/**** ShellWindow object ****/
/**********************************/

__declspec(naked) void ShellWindow_QueryInterface(SHELLWINDOW_OBJ *shellwindow, struct _GUID *guid, void **container) {
	PROLOGUE

	shellwindow->iface->QueryInterface_ad40((HANDLE)shellwindow, guid, container);

	EPILOGUE
}