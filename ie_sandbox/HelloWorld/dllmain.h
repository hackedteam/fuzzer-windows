// dllmain.h : Declaration of module class.

class CHelloWorldModule : public ATL::CAtlDllModuleT< CHelloWorldModule >
{
public :
	DECLARE_LIBID(LIBID_HelloWorldLib)
	DECLARE_REGISTRY_APPID_RESOURCEID(IDR_HELLOWORLD, "{8732C9A3-5067-42C8-A23D-686D3142B773}")
};

extern class CHelloWorldModule _AtlModule;
