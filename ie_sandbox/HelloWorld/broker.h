#include <ShellAPI.h>


// CoCreateUserBroker() function in ieframe.dll
#define COCREATEUSERBROKER_ENTRY 58


typedef struct tagProxyResolveUrl {	
	unsigned char *url;
	unsigned char *domain;
	unsigned int a;
	unsigned int b;
	unsigned int c;
	unsigned int d;
	unsigned char *buffer;
};




/************************************/
/*** REMOTE INTERFACES **************/
/************************************/


// [1] 
// IEUserBroker interface (ieframe.dll).
// We need it to communicate with the renderer's father
typedef struct IEUserBroker {
	void (*queryInterface)(HANDLE, struct _GUID *, void *); 
	void (*addRef)(HANDLE);  
	void (*release)(HANDLE);           
	void (*initialize)(HANDLE, long, long, void *);
	void (*CreateProcessW)(HANDLE, unsigned long, unsigned short *,unsigned short *,unsigned long, unsigned long, unsigned char const *,unsigned short *, LPSTARTUPINFO /* OK (_BROKER_STARTUINFOEXW *) */,_PROCESS_INFORMATION *);
	void (*WinExec)(HANDLE, unsigned long, char const *,unsigned int, unsigned int *);
	void (*createKnownObject)(HANDLE, struct _GUID *, struct _GUID *, void *);
	void (*BrokerCoCreateInstance)(HANDLE, unsigned long, _GUID *, IUnknown *, unsigned long, _GUID *, IUnknown * *);
	void (*BrokerCoCreateInstanceEx)(HANDLE, unsigned long, _GUID *, IUnknown *, unsigned long, _COSERVERINFO *, unsigned long, tagMULTI_QI * /* OK (tagBROKER_MULTI_QI *) */);
	void (*BrokerCoGetClassObject)(HANDLE, unsigned long, _GUID *, unsigned long, _COSERVERINFO *, _GUID *, IUnknown * *);
} IEUSER_BROKER, *IE_USER_BROKER_IFACE;


typedef struct IEUserBroker_obj {
	IE_USER_BROKER_IFACE iface;
	int a;
	void *p1;
	void *p2;
	void *p3;
} IE_USER_BROKER_OBJ;



// [2]
// CProtectedModeAPI interface (ieframe.dll).
// Remote interface for implementing the protected mode APIs requiring the broker service
typedef struct CProtectedModeAPI {
	void (*QueryInterface)(HANDLE, _GUID *,void * *);
	void (*AddRef)(HANDLE);
	void (*Release)(HANDLE);
	void (*ShowSaveFileDialog)(HANDLE, HANDLE ,LPWSTR, LPWSTR, LPCWSTR,LPCWSTR, DWORD, DWORD, LPWSTR *);
	void (*SaveFileAs)(HANDLE, unsigned short const *);
	void (*RegCreateKeyExW)(HANDLE, unsigned long,unsigned short const *,unsigned long,unsigned long *,unsigned long *);
	void (*RegSetValueExW)(HANDLE, unsigned short const *,unsigned short const *,unsigned long,unsigned char const *,unsigned long);
	void (*destructor)(HANDLE, unsigned int);
} PROTECTED_MODE_API, *PROTECTED_MODE_IFACE;

typedef struct ProtectedModeAPI_obj {
	PROTECTED_MODE_IFACE iface;
	int a;
	void *p1;
	void *p2;
	void *p3;
} PROTECTED_MODE_OBJ;


// [3]
// CStdIdentity Interface (ole32.dll).
// We need it to get every other interface
typedef struct CStdIdentity {
	void (*QueryInterface)(HANDLE, _GUID *,void * *);
	void (*AddRef)(HANDLE);
	void (*Release)(HANDLE);
	void (*QueryInternalInterface)(HANDLE, _GUID *,void * *);
} STD_IDENTITY, *STD_IDENTITY_IFACE;

typedef struct StdIdentity_obj {
	STD_IDENTITY_IFACE iface;
	int a;
	void *p1;
	void *p2;
	void *p3;
} STD_IDENTITY_OBJ;



// [4]
// ShDocvwBroker interface (ieframe.dll).
// The core of the broker service. It exports more than 100 available remote methods
typedef struct ShBroker {
	void (*QueryInterface)(HANDLE, _GUID *,void * *);
	void (*AddRef)(HANDLE);
	void (*Release)(HANDLE);
	void (*RedirectUrl)(HANDLE, unsigned short const *,unsigned long, void */*(_BROKER_REDIRECT_DETAIL *)*/, void */*(IXMicTestMode *)*/);
	void (*RedirectShortcut)(HANDLE, unsigned short const *,unsigned short const *,unsigned long, void * /*(_BROKER_REDIRECT_DETAIL *)*/);
	void (*RedirectUrlWithBindInfo)(HANDLE, _tagBINDINFO * /* CHECK (_BROKER_BIND_INFO *)*/,void * /*(_BROKER_REDIRECT_DETAIL *)*/,void */*(IXMicTestMode *)*/);
	void (*ShowInternetOptions)(HANDLE, HWND__ *,unsigned short const *,unsigned short const *,long, _ITEMIDLIST * /* CHECK (_ITEMIDLIST_ABSOLUTE * *)*/,unsigned long,int *);
	void (*ShowInternetOptionsZones)(HANDLE, HWND__ *,unsigned short const *,unsigned short const *);
	void (*ShowInternetOptionsLanguages)(HANDLE, HANDLE);
	void (*ShowPopupManager)(HANDLE, HWND__ *,unsigned short const *);
	void (*ConfigurePopupExemption)(HANDLE, HWND__ *,int,unsigned short const *,int *);
	void (*ConfigurePopupMgr)(HANDLE, HWND__ *,int);
	void (*RemoveFirstHomePage)(HANDLE);
	void (*SetHomePage)(HANDLE, HWND__ *,long, _ITEMIDLIST * /* CHECK (_ITEMIDLIST_ABSOLUTE * *)*/,long);
	void (*RemoveHomePage)(HANDLE, HWND__ *,int);
	void (*FixInternetSecurity)(HANDLE, HWND__ *,int *);
	void (*ShowManageAddons)(HANDLE, HWND__ *,unsigned long,_GUID *,unsigned int,int);
	void (*CacheExtFileVersion)(HANDLE, _GUID const &,unsigned short const *);
	void (*ShowAxApprovalDlg)(HANDLE, HWND__ *,_GUID const &,int,unsigned short const *,unsigned short const *,unsigned short const *);
	void (*SendLink)(HANDLE, _ITEMIDLIST * /* CHECK (_ITEMIDLIST_ABSOLUTE * *)*/, unsigned short const *);
	void (*SendPage)(HANDLE, HWND__ *,IDataObject *);
	void (*NewMessage)(HANDLE);
	void (*ReadMail)(HANDLE, HWND__ *);
	void (*SetAsBackground)(HANDLE, unsigned short const *);
	void (*ShowSaveBrowseFile)(HANDLE, HWND__ *,unsigned short const *,unsigned short const *,int,int,unsigned short * *,unsigned long *,unsigned long *);
	void (*SaveAsComplete)(HANDLE);
	void (*SaveAsFile)(HANDLE);
	void (*StartImportExportWizard)(HANDLE, int,HWND__ *);
	void (*EditWith)(HANDLE, HWND__ *,unsigned long,unsigned long,unsigned long,unsigned short const *,unsigned short const *,unsigned short const *);
	void (*ShowSaveImage)(HANDLE, HWND__ *,unsigned short const *,unsigned long,unsigned short * *);
	void (*SaveImage)(HANDLE, unsigned short const *);
	void (*CreateShortcutOnDesktop)(HANDLE, HWND__ *, _ITEMIDLIST const * /* CHECK (_ITEMIDLIST_ABSOLUTE * *)*/,unsigned short const *,IOleCommandTarget *);
	void (*ShowSynchronizeUI)(HANDLE);
	void (*OpenFolderAndSelectItem)(HANDLE, unsigned short const *);
	void (*DoGetOpenFileNameDialog)(HANDLE, /*(_SOpenDlg *)*/ void *);
	void (*ShowSaveFileName)(HANDLE, HWND__ *,unsigned short const *,unsigned short const *,unsigned short const *,unsigned short const *,unsigned int,unsigned short *,unsigned long,unsigned short const *,unsigned short * *);
	void (*SaveFile)(HANDLE, HWND__ *,unsigned int,unsigned long);
	void (*VerifyTrustAndExecute)(HANDLE, HWND__ *,unsigned short const *,unsigned short const *);
	void (*GetFeedByUrl)(HANDLE, unsigned short const *,unsigned short * *);
	void (*BrokerAddToFavoritesEx)(HANDLE, HWND__ *, _ITEMIDLIST const * /* CHECK (_ITEMIDLIST_ABSOLUTE * *)*/,unsigned short const *,unsigned long,IOleCommandTarget *,unsigned short *,unsigned long,unsigned short const *);
	void (*Subscribe)(HANDLE, HWND__ *,unsigned short const *,unsigned short const *,int,int,int);
	void (*MarkAllItemsRead)(HANDLE, unsigned short const *);
	void (*MarkItemsRead)(HANDLE, unsigned short const *,unsigned int *,unsigned int);
	void (*Properties)(HANDLE, HWND__ *,unsigned short const *);
	void (*DeleteFeedItem)(HANDLE, HWND__ *,unsigned short const *,unsigned int);
	void (*DeleteFeed)(HANDLE, HWND__ *,unsigned short const *);
	void (*DeleteFolder)(HANDLE, HWND__ *,unsigned short const *);
	void (*Refresh)(HANDLE, unsigned short const *);
	void (*MoveFeed)(HANDLE, HWND__ *,unsigned short const *,unsigned short const *);
	void (*MoveFeedFolder)(HANDLE, HWND__ *,unsigned short const *,unsigned short const *);
	void (*RenameFeed)(HANDLE, HWND__ *,unsigned short const *,unsigned short const *);
	void (*RenameFeedFolder)(HANDLE, HWND__ *,unsigned short const *,unsigned short const *);
	void (*NewFeedFolder)(HANDLE, unsigned short const *);
	void (*FeedRefreshAll)(HANDLE);
	void (*ShowFeedAuthDialog)(HANDLE, HWND__ *,unsigned short const *, /*(tagFEEDTASKS_AUTHTYPE)*/ void *);
	void (*ShowAddSearchProvider)(HANDLE, HWND__ *,unsigned short const *,unsigned short const *,int);
	void (*InitHKCUSearchScopesRegKey)(HANDLE);
	void (*DoShowDeleteBrowsingHistoryDialog)(HANDLE, HWND__ *);
	void (*ResetInternetOptions)(HANDLE);
	void (*StartAutoProxyDetection)(HANDLE);
	void (*ForceNexusLookup)(HANDLE);
	void (*SetAutoConnectOption)(HANDLE, unsigned short const *,unsigned long);
	void (*EditAntiPhishingOptinSetting)(HANDLE, HWND__ *,unsigned long,int *);
	void (*ShowMyPictures)(HANDLE);
	void (*ChangeIntranetSettings)(HANDLE, HWND__ *,int);
	void (*FixProtectedModeSettings)(HANDLE);
	void (*ShowAddService)(HANDLE, HWND__ *,unsigned short const *,unsigned short const *,int);
	void (*ShowAddWebFilter)(HANDLE, HWND__ *,unsigned short const *,unsigned short const *,unsigned short const *);
	void (*DoBrowserRegister)(HANDLE, IDispatch *,long,int,long *);
	void (*DoBrowserRevoke)(HANDLE, long);
	void (*DoOnNavigate)(HANDLE, long,tagVARIANT *);
	void (*AddDesktopComponent)(HANDLE, unsigned short *,unsigned short *,tagVARIANT *,tagVARIANT *,tagVARIANT *,tagVARIANT *);
	void (*DoOnCreated)(HANDLE, long,IUnknown *);
	void (*GetShellWindows)(HANDLE, /*(OUT)*/ IUnknown * *);
	void (*RestoreTab)(HANDLE, long,unsigned long,long);
	void (*SetPositionCookie)(HANDLE, unsigned long);
	void (*IsProtectedModeUrl)(HANDLE, unsigned short const *);
	void (*DoDiagnoseConnectionProblems)(HANDLE, HWND__ *,unsigned short *,unsigned short *);
	void (*PerformDoDragDrop)(HANDLE, HWND__ *, /*(IEDataObjectWrapper *)*/ void *, /*(IEDropSourceWrapper *)*/ void *,unsigned long,unsigned long,unsigned long *,long *);
	void (*TurnOnFeedSyncEngine)(HANDLE, HWND__ *);
	void (*InternetSetPerSiteCookieDecisionW)(HANDLE, unsigned short const *,unsigned long);
	void (*ConfirmCookie)(HANDLE, HWND__ *,unsigned long,unsigned long,/*(_BROKER_COOKIE_DLG_INFO *)*/ void *);
	void (*SetAttachmentUserOverride)(HANDLE, unsigned short const *);
	void (*WriteClassesOfCategory)(HANDLE, _GUID const &,int);
	void (*BrokerSetFocus)(HANDLE, unsigned long,HWND__ *);
	void (*BrokerShellNotifyIconA)(HANDLE, unsigned long,/* OK (_BROKER_NOTIFYICONDATAA *)*/ NOTIFYICONDATA *);
	void (*BrokerShellNotifyIconW)(HANDLE, unsigned long,/* OK (_BROKER_NOTIFYICONDATAA *)*/ NOTIFYICONDATA *);
	void (*DisplayVirtualizedFolder)(HANDLE);
	void (*BrokerSetWindowPos)(HANDLE, HWND__ *,HWND__ *,int,int,int,int,unsigned int);
	void (*WriteUntrustedControlDetails)(HANDLE, _GUID const &,unsigned short const *,unsigned short const *,unsigned long,unsigned char *);
	void (*SetComponentDeclined)(HANDLE, char const *,char const *);
	void (*DoShowPrintDialog)(HANDLE, /*OUT (_BROKER_PRINTDLG *)*/ void *);
	void (*NavigateHomePages)(HANDLE);
	void (*ShowAxDomainApprovalDlg)(HANDLE, HWND__ *,_GUID const &,int,unsigned short const *,unsigned short const *,unsigned short const *,unsigned short const *);
	void (*ActivateExtensionFromCLSID)(HANDLE, HWND__ *,unsigned short const *,unsigned long,unsigned int,unsigned int);
	void (*BrokerCoCreateNewIEWindow)(HANDLE, unsigned long,_GUID const &,void * *,int,unsigned long);
	void (*BeginFakeModalityForwardingToTab)(HANDLE, HWND__ *,long);
	void (*BrokerEnableWindow)(HANDLE, int,int *);
	void (*EndFakeModalityForwardingToTab)(HANDLE, HWND__ *,long);
	void (*CloseOldTabIfFailed)(HANDLE);
	void (*GetGuidsForConnectedNetworks)(HANDLE, unsigned long *,unsigned short * * *,unsigned short * * *,unsigned short * * *,unsigned long *,unsigned long *);
	void (*EnableSuggestedSites)(HANDLE, HWND__ *,int);
	void (*SetProgressValue)(HANDLE, HWND__ *,unsigned long,unsigned long);
	void (*BrokerStartNewIESession)(HANDLE);
	void (*CompatDetachInputQueue)(HANDLE, HWND__ *);
	void (*CompatAttachInputQueue)(HANDLE);
	void (*SetToggleKeys)(HANDLE, unsigned long);
	void (*RepositionInfrontIE)(HANDLE, HWND__ *,int,int,int,int,unsigned int);
	void (*AddSessionIE7Rule)(HANDLE, unsigned short const *);
	void (*ReportShipAssert)(HANDLE, unsigned long,unsigned long,unsigned long,unsigned short const *,unsigned short const *,unsigned short const *);
	void (*AutoProxyGetProxyForUrl)(HANDLE, /*(tagProxyResolveUrl *)*/ tagProxyResolveUrl *, /* OUT (tagProxyResult *)*/ void *);
	void (*AutoProxyReportRequestResults)(HANDLE, int,/*(tagProxyResolveUrl *)*/ tagProxyResolveUrl *,/* OUT (tagProxyResult *)*/ void *);
	void (*ShowOpenSafeOpenDialog)(HANDLE, HWND__ *,/*(_BROKER_SAFEOPENDLGPARAM *)*/ void *,unsigned int *,unsigned int *);
	void (*BrokerAddSiteToStartMenu)(HANDLE, HWND__ *,unsigned short *,unsigned short const *,long,unsigned long);
	void (*SiteModeAddThumbnailButton)(HANDLE, unsigned int *,HWND__ *,unsigned short *,unsigned short const *);
	void (*SiteModeAddButtonStyle)(HANDLE, int *,HWND__ *,unsigned int,unsigned short *,unsigned short const *);
	void (*IsSiteModeFirstRun)(HANDLE, int,unsigned short *);
	void (*BrokerDoSiteModeDragDrop)(HANDLE, unsigned long,long *,unsigned long *);
	void (*EnterUILock)(HANDLE, long);
	void (*LeaveUILock)(HANDLE, long);
	void (*destructor)(HANDLE, unsigned int);
} SHBROKER, *SHBROKER_IFACE;


typedef struct ShBroker_obj {
	SHBROKER_IFACE iface;
	int a;
	void *p1;
	void *p2;
	void *p3;
} SH_BROKER_OBJ;



// [5]
// IERecoveryStore (ieframe.dll)
typedef struct IERecoveryStore {
	void (*QueryInterface)(HANDLE, _GUID *,void * *);
	void (*AddRef)(HANDLE);
	void (*Release)(HANDLE);
	void (*Initialize)(HANDLE, unsigned long, _GUID *,unsigned long,unsigned short const *);
	void (*InitializeFromFile)(HANDLE, unsigned short const *,_GUID *,unsigned long);
	void (*CreateFrame)(HANDLE, unsigned int *,unsigned long,unsigned long);
	void (*CloseFrame)(HANDLE, unsigned int);
	void (*GetFrameCount)(HANDLE, unsigned int *);
	void (*GetFrameId)(HANDLE, unsigned int,unsigned int *);
	void (*GetFrameIESession)(HANDLE, unsigned int,unsigned long *,unsigned long *);
	void (*CreateTab)(HANDLE, unsigned int,unsigned short const *,/* OUT (ITabRecoveryData * *)*/ void **);
	void (*CloseTab)(HANDLE, unsigned int,_GUID const &);
	void (*GetTabCount)(HANDLE, unsigned int,unsigned int *);
	void (*GetTab)(HANDLE, unsigned int,unsigned int,/* OUT (ITabRecoveryData * *)*/ void **);
	void (*GetCount)(HANDLE, long *);
	void (*GetClosedTab)(HANDLE, _GUID *,/* OUT (ITabRecoveryData * *)*/ void **);
	void (*DeleteClosedTab)(HANDLE, _GUID const &);
	void (*Recover)(HANDLE, /* NULL(ITabWindowManager *)*/ void *,unsigned long);
	void (*RecoverFrame)(HANDLE,/*NULL (ITabWindowManager *)*/ void *,unsigned long,unsigned int);
	void (*Flush)(HANDLE);
	void (*DeleteSelf)(HANDLE);
	void (*DeleteAllTabs)(HANDLE);
	void (*DeleteOnLastRelease)(HANDLE);
	void (*Shutdown)(HANDLE);
	void (*Restart)(HANDLE);
	void (*IsShutdown)(HANDLE, int *);
	void (*IsRestart)(HANDLE, int *);
	void (*GetID)(HANDLE, long *);
	void (*IsInPrivate)(HANDLE, int *);
	void (*IsExtOff)(HANDLE, int *);
	void (*GetFrameCLSID)(HANDLE, _GUID *);
	void (*SetActiveTab)(HANDLE, unsigned int,_GUID const &);
	void (*GetActiveTab)(HANDLE, unsigned int,_GUID *);
	void (*SwitchTabFrame)(HANDLE, unsigned int,unsigned int,_GUID const &);
	void (*DeleteExistingStores)(HANDLE);
	void (*FindCrashedSessions)(HANDLE, int *,int *);
} IERECOVERY_STORE, *IERECOVERY_STORE_IFACE;

typedef struct IERecoveryStore_obj {
	IERECOVERY_STORE_IFACE iface;
	int a;
	void *p1;
	void *p2;
	void *p3;
} IERECOVERY_STORE_OBJ;



// [6]
// IEAxInstallBroker (ieframe.dll)
typedef struct IeAxInstallBroker {
	void (*QueryInterface_ad12)(HANDLE, _GUID *,void * *);
	void (*AddRef_ad12)(HANDLE);
	void (*Release_ad12)(HANDLE);
	void (*BrokerGetAxInstallBroker)(HANDLE, _GUID *,_GUID *,HWND__ *,unsigned long,IUnknown * *);
} IEAXINSTALLBROKER, *IEAXINSTALLBROKER_IFACE;

typedef struct IEAxInstallBroker_obj {
	IEAXINSTALLBROKER_IFACE iface;
	int a;
	void *p1;
	void *p2;
	void *p3;
} IEAXINSTALLBROKER_OBJ;


// [7]
// SettingsStore (ieutil.dll)
typedef struct SettingsStore {
	void (*QueryInterface)(HANDLE, _GUID *,void * *);
	void (*AddRef)(HANDLE);
	void (*Release)(HANDLE);
	void (*SetValue)(HANDLE, _GUID *,int,int,unsigned char *,unsigned long);
	void (*SetExtValue)(HANDLE, _GUID *,int,int,tagSAFEARRAY *,unsigned char *,unsigned long);
	void (*DeleteValue)(HANDLE, _GUID *,int);
	void (*DeleteExtValue)(HANDLE, _GUID *,int,tagSAFEARRAY *);
	void (*DeleteKey)(HANDLE, _GUID *,int);
	void (*DeleteExtKey)(HANDLE, _GUID *,int,tagSAFEARRAY *);
} SETTINGSSTORE, *SETTINGSSTORE_IFACE;

typedef struct SettingsStore_obj {
	SETTINGSSTORE_IFACE iface;
	int a;
	void *p1;
	void *p2;
	void *p3;
} SETTINGSSTORE_OBJ;



// [8]
// IERegHelperBroker (ieframe.dll)
typedef struct IERegHelperBroker {
	void (*QueryInterface_ad4)(HANDLE, _GUID *,void * *);
	void (*AddRef_ad4)(HANDLE);
	void (*Release_ad4)(HANDLE);
	void (*DoDelSingleValue)(HANDLE, unsigned long);
	void (*DoDelIndexedValue)(HANDLE, unsigned long,unsigned long);
	void (*DoSetSingleValue)(HANDLE, unsigned long,unsigned char *,unsigned long);
	void (*DoSetIndexedValue)(HANDLE, unsigned long,unsigned long,unsigned char *,unsigned long);
	void (*Reduce)(HANDLE, IBindCtx *,unsigned long,IMoniker * *,IMoniker * *);
	void (*DoCreateKey)(HANDLE, unsigned long);
} IEREGHELPER_BROKER, *IEREGHELPER_BROKER_IFACE;

typedef struct IERegHelperBroker_obj {
	IEREGHELPER_BROKER_IFACE iface;
	int a;
	void *p1;
	void *p2;
	void *p3;
} IEREGHELPER_BROKER_OBJ;


// [9]
// IERegHelperCleanup (ieframe.dll)
typedef struct IERegHelperCleanup {
	void (*QueryInterface_ad8)(HANDLE, _GUID *,void * *);
	void (*AddRef_ad8)(HANDLE);
	void (*Release_ad8)(HANDLE);
	void (*RegisterCleanup)(HANDLE, /*(IeRegHelperObjectCleanup *)*/ IUnknown *);
} IEREGHELPER_CLEANUP, *IEREGHELPER_CLEANUP_IFACE;

typedef struct IERegHelperCleanup_obj {
	IEREGHELPER_CLEANUP_IFACE iface;
	int a;
	void *p1;
	void *p2;
	void *p3;
} IEREGHELPER_CLEANUP_OBJ;


//[10]
//IeBrokerAttach (ieframe.dll)
typedef struct IeBrokerAttach {
	void (*QueryInterface_ad16)(HANDLE, _GUID *,void * *);
	void (*AddRef_ad16)(HANDLE);	
	void (*Release_ad16)(HANDLE);
	void (*AttachIEFrameToBroker)(HANDLE, IUnknown *);
} IEBROKERATTACH, *IEBROKERATTACH_IFACE;

// IeBrokerAttach object
typedef struct IEBrokerAttach_obj {
	IEBROKERATTACH_IFACE iface;
	int a;
	void *p1;
	void *p2;
	void *p3;
} IEBROKERATTACH_OBJ;


// [11]
// FeedsArbiterLoriBroker interface (msfeeds.dll)
// No symbols
typedef struct FeedsArbiterLoriBroker {
	void (*m0)(HANDLE, ...);
	void (*m1)();
	void (*m2)();
	void (*m3)();
	void (*m4)(HANDLE, ...);
} FEEDSARBITERLORI_BROKER, *FEEDSARBITERLORI_BROKER_IFACE;

typedef struct FeedsArbiterLoriBroker_obj {
	FEEDSARBITERLORI_BROKER_IFACE iface;
	int a;
	void *p1;
	void *p2;
	void *p3;
} FEEDSARBITERLORI_BROKER_OBJ;


// [12]
// FeedsLoriBroker interface (msfeeds.dll)
// No symbols
typedef struct FeedsLoriBroker {
	void (*m0)(HANDLE, ...);
	void (*m1)(HANDLE, ...);
	void (*m2)(HANDLE, ...);
	void (*m3)(HANDLE, ...);
	void (*m4)(HANDLE, ...);
	void (*m5)(HANDLE, ...);
	void (*m6)(HANDLE, ...);
	void (*m7)(HANDLE, ...);
	void (*m8)(HANDLE, ...);
	void (*m9)(HANDLE, ...);
	void (*m10)(HANDLE, ...);
} FEEDSLORI_BROKER, *FEEDSLORI_BROKER_IFACE;

typedef struct FeedsLoriBroker_obj {
	FEEDSLORI_BROKER_IFACE iface;
	int a;
	void *p1;
	void *p2;
	void *p3;
} FEEDSLORI_BROKER_OBJ;


// [13]
// IShellWindow interface (iertutil.dll)

typedef struct ShellWindow {
	void (*QueryInterface_ad40 )(HANDLE, _GUID *,void * *);
	void (*AddRef_ad40)(HANDLE);
	void (*Release_ad40 )(HANDLE);
	void (*get_alinkColor)(HANDLE, tagVARIANT *);
	void (*SetMenuSB)(HANDLE, HMENU__ *,void *,HWND__ *);
	void (*UpdateEntryEx)(HANDLE, IUnknown *,int,int,int,int);
	void (*Invoke)(HANDLE, long,_GUID const &,unsigned long,unsigned short,tagDISPPARAMS *,tagVARIANT *,tagEXCEPINFO *,unsigned int *);
	void (*get_alinkColor2)(HANDLE, tagVARIANT *);
	void (*UpdateEntryEx2)(HANDLE, IUnknown *,int,int,int,int);
	void (*SetSearchTerm)(HANDLE, unsigned short *);
	void (*Register)(HANDLE, IDispatch *,long,int,long *);
	void (*RegisterPending)(HANDLE, long,tagVARIANT *,tagVARIANT *,int,long *);
	void (*Revoke)(HANDLE, long);
	void (*AddEntry)(HANDLE, IUnknown *,int);
	void (*AddEntry2)(HANDLE, IUnknown *,int);
	void (*FindWindowSW)(HANDLE, tagVARIANT *,tagVARIANT *,int,long *,int, IDispatch * *);
	void (*OnCreated)(HANDLE, long,IUnknown *);
	void (*get_alinkColor3)(HANDLE, tagVARIANT *);
} SHELLWINDOW, *SHELLWINDOW_IFACE;

typedef struct ShellWindow_Obj {
	SHELLWINDOW_IFACE iface;
	int a;
	void *p1;
	void *p2;
	void *p3;
} SHELLWINDOW_OBJ;



// Get the IEUserBroker interface (tested)
IE_USER_BROKER_OBJ* getUserBrokerInterface();
// Get the ProtecteModeAPI interface (tested)
PROTECTED_MODE_OBJ* getProtectedModeAPIInterface();
// Get the ShDocvwBroker interface (tested)
SH_BROKER_OBJ* getShBrokerIface();
// Get the IERecoveryStore interface (tested)
IERECOVERY_STORE_OBJ* getRecoveryStoreIface();
// Get the SettingsStore interface (tested)
SETTINGSSTORE_OBJ* getSettingsStoreIface();
// Get the IERegHelperBroker interface (tested)
IEREGHELPER_BROKER_OBJ* getIERegHelperBrokerIface();
// Get the IERegHelperCleanup interface (not working)
IEREGHELPER_CLEANUP_OBJ* getIERegHelperCleanupIface();
// Get the IEBrokerAttach interface (tested)
IEBROKERATTACH_OBJ* getIEBrokerAttachIface();
// Get the IEAxInstallBroker interface (tested)
IEAXINSTALLBROKER_OBJ* getIEAxInstallBrokerIface();
// Get the FeedsLoriBroker interface (tested)
FEEDSLORI_BROKER_OBJ* getFeedsLoriBrokerIface();
// Get the FeedsArbiterLoriBroker interface (tested)
FEEDSARBITERLORI_BROKER_OBJ* getFeedsArbiterLoriBrokerIface();
// Get the ShellWindow interface (tested)
SHELLWINDOW_OBJ* getShellWindowIface();



/***** BROKER CALL WRAPPERS ************/

/*****************************/
/**** IEUserBroker object ****/
/*****************************/

void IEUserBroker_QueryInterface(IE_USER_BROKER_OBJ *, struct _GUID *, void *);
void IEUserBroker_Initialize(IE_USER_BROKER_OBJ *, long, long, void *);
void IEUserBroker_CreateKnownObject(IE_USER_BROKER_OBJ *, struct _GUID *, struct _GUID *, void *);

/*****************************/
/**** StdIdentity object *****/
/*****************************/

void CStdIdentity_QueryInterfaces(STD_IDENTITY_OBJ *, struct _GUID *, void **);
void CStdIdentity_QueryInternalInterface(STD_IDENTITY_OBJ *, struct _GUID *, void **);

/*********************************/
/**** ProtectedModeAPI object ****/
/*********************************/


void ProtectedModeAPI_ShowDialog(PROTECTED_MODE_OBJ *, HANDLE, LPWSTR, LPWSTR, LPCWSTR, LPCWSTR, DWORD, DWORD, LPWSTR *);
void ProtectedModeAPI_QueryInterface(PROTECTED_MODE_OBJ *, struct _GUID *, void **);

/******************************/
/**** ShdocvwBroker object ****/
/******************************/

void ShBroker_QueryInterface(SH_BROKER_OBJ *, struct _GUID *, void **);
void ShBroker_ShowLang(SH_BROKER_OBJ *, HANDLE);


/********************************/
/**** IESettingsStore object ****/
/********************************/

void SettingsStore_QueryInterface(SETTINGSSTORE_OBJ *, struct _GUID *, void **);
void SettingsStore_DeleteValue(SETTINGSSTORE_OBJ *, _GUID *, int);

/********************************/
/**** IERecoveryStore object ****/
/********************************/

void IERecoveryStore_QueryInterface(IERECOVERY_STORE_OBJ *, struct _GUID *, void **);
void IERecoveryStore_Shutdown(IERECOVERY_STORE_OBJ *);

/********************************/
/**** IERegHelperBroker object ****/
/********************************/

void IERegHelperBroker_QueryInterface(IEREGHELPER_BROKER_OBJ *, struct _GUID *, void **);
void IERegHelperBroker_DoCreateKey(IEREGHELPER_BROKER_OBJ *, int);

/********************************/
/**** IERegHelperCleanup object ****/
/********************************/

void IERegHelperCleanup_QueryInterface(IEREGHELPER_CLEANUP_OBJ *, struct _GUID *, void **);
void IERegHelperCleanup_RegisterCleanup(IEREGHELPER_CLEANUP_OBJ *, IUnknown *);

/********************************/
/**** IEBrokerAttach object ****/
/********************************/

void IEBrokerAttach_QueryInterface(IEBROKERATTACH_OBJ *, struct _GUID *, void **);
void IEBrokerAttach_AttachIEFrameToBroker(IEBROKERATTACH_OBJ* , IUnknown *);


/***********************************/
/**** IEAxInstallBroker object ****/
/**********************************/

void IEAxInstallBroker_QueryInterface(IEAXINSTALLBROKER_OBJ *, struct _GUID *, void **);
void IEAxInstallBroker_GetAxInstallBroker(IEAXINSTALLBROKER_OBJ *, HWND *, IUnknown **);

/***********************************/
/**** FeedsLoriBroker object ****/
/**********************************/

void FeedsLori_QueryInterface(FEEDSLORI_BROKER_OBJ *, struct _GUID *, void **);

/***********************************/
/**** FeedsArbiretLoriBroker object ****/
/**********************************/

void FeedsArbiterLori_QueryInterface(FEEDSARBITERLORI_BROKER_OBJ *, struct _GUID *, void **);

/***********************************/
/**** ShellWindow object ****/
/**********************************/

void ShellWindow_QueryInterface(SHELLWINDOW_OBJ *, struct _GUID *, void **);