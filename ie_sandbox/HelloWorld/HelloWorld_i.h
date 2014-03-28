

/* this ALWAYS GENERATED file contains the definitions for the interfaces */


 /* File created by MIDL compiler version 7.00.0555 */
/* at Mon Dec 09 09:34:43 2013
 */
/* Compiler settings for HelloWorld.idl:
    Oicf, W1, Zp8, env=Win32 (32b run), target_arch=X86 7.00.0555 
    protocol : dce , ms_ext, c_ext, robust
    error checks: allocation ref bounds_check enum stub_data 
    VC __declspec() decoration level: 
         __declspec(uuid()), __declspec(selectany), __declspec(novtable)
         DECLSPEC_UUID(), MIDL_INTERFACE()
*/
/* @@MIDL_FILE_HEADING(  ) */

#pragma warning( disable: 4049 )  /* more than 64k source lines */


/* verify that the <rpcndr.h> version is high enough to compile this file*/
#ifndef __REQUIRED_RPCNDR_H_VERSION__
#define __REQUIRED_RPCNDR_H_VERSION__ 475
#endif

#include "rpc.h"
#include "rpcndr.h"

#ifndef __RPCNDR_H_VERSION__
#error this stub requires an updated version of <rpcndr.h>
#endif // __RPCNDR_H_VERSION__

#ifndef COM_NO_WINDOWS_H
#include "windows.h"
#include "ole2.h"
#endif /*COM_NO_WINDOWS_H*/

#ifndef __HelloWorld_i_h__
#define __HelloWorld_i_h__

#if defined(_MSC_VER) && (_MSC_VER >= 1020)
#pragma once
#endif

/* Forward Declarations */ 

#ifndef __IHelloWorldBHO_FWD_DEFINED__
#define __IHelloWorldBHO_FWD_DEFINED__
typedef interface IHelloWorldBHO IHelloWorldBHO;
#endif 	/* __IHelloWorldBHO_FWD_DEFINED__ */


#ifndef __HelloWorldBHO_FWD_DEFINED__
#define __HelloWorldBHO_FWD_DEFINED__

#ifdef __cplusplus
typedef class HelloWorldBHO HelloWorldBHO;
#else
typedef struct HelloWorldBHO HelloWorldBHO;
#endif /* __cplusplus */

#endif 	/* __HelloWorldBHO_FWD_DEFINED__ */


/* header files for imported files */
#include "oaidl.h"
#include "ocidl.h"

#ifdef __cplusplus
extern "C"{
#endif 


#ifndef __IHelloWorldBHO_INTERFACE_DEFINED__
#define __IHelloWorldBHO_INTERFACE_DEFINED__

/* interface IHelloWorldBHO */
/* [unique][nonextensible][dual][uuid][object] */ 


EXTERN_C const IID IID_IHelloWorldBHO;

#if defined(__cplusplus) && !defined(CINTERFACE)
    
    MIDL_INTERFACE("3CF024C9-C59C-478E-8759-4171F2613CAD")
    IHelloWorldBHO : public IDispatch
    {
    public:
    };
    
#else 	/* C style interface */

    typedef struct IHelloWorldBHOVtbl
    {
        BEGIN_INTERFACE
        
        HRESULT ( STDMETHODCALLTYPE *QueryInterface )( 
            IHelloWorldBHO * This,
            /* [in] */ REFIID riid,
            /* [annotation][iid_is][out] */ 
            __RPC__deref_out  void **ppvObject);
        
        ULONG ( STDMETHODCALLTYPE *AddRef )( 
            IHelloWorldBHO * This);
        
        ULONG ( STDMETHODCALLTYPE *Release )( 
            IHelloWorldBHO * This);
        
        HRESULT ( STDMETHODCALLTYPE *GetTypeInfoCount )( 
            IHelloWorldBHO * This,
            /* [out] */ UINT *pctinfo);
        
        HRESULT ( STDMETHODCALLTYPE *GetTypeInfo )( 
            IHelloWorldBHO * This,
            /* [in] */ UINT iTInfo,
            /* [in] */ LCID lcid,
            /* [out] */ ITypeInfo **ppTInfo);
        
        HRESULT ( STDMETHODCALLTYPE *GetIDsOfNames )( 
            IHelloWorldBHO * This,
            /* [in] */ REFIID riid,
            /* [size_is][in] */ LPOLESTR *rgszNames,
            /* [range][in] */ UINT cNames,
            /* [in] */ LCID lcid,
            /* [size_is][out] */ DISPID *rgDispId);
        
        /* [local] */ HRESULT ( STDMETHODCALLTYPE *Invoke )( 
            IHelloWorldBHO * This,
            /* [in] */ DISPID dispIdMember,
            /* [in] */ REFIID riid,
            /* [in] */ LCID lcid,
            /* [in] */ WORD wFlags,
            /* [out][in] */ DISPPARAMS *pDispParams,
            /* [out] */ VARIANT *pVarResult,
            /* [out] */ EXCEPINFO *pExcepInfo,
            /* [out] */ UINT *puArgErr);
        
        END_INTERFACE
    } IHelloWorldBHOVtbl;

    interface IHelloWorldBHO
    {
        CONST_VTBL struct IHelloWorldBHOVtbl *lpVtbl;
    };

    

#ifdef COBJMACROS


#define IHelloWorldBHO_QueryInterface(This,riid,ppvObject)	\
    ( (This)->lpVtbl -> QueryInterface(This,riid,ppvObject) ) 

#define IHelloWorldBHO_AddRef(This)	\
    ( (This)->lpVtbl -> AddRef(This) ) 

#define IHelloWorldBHO_Release(This)	\
    ( (This)->lpVtbl -> Release(This) ) 


#define IHelloWorldBHO_GetTypeInfoCount(This,pctinfo)	\
    ( (This)->lpVtbl -> GetTypeInfoCount(This,pctinfo) ) 

#define IHelloWorldBHO_GetTypeInfo(This,iTInfo,lcid,ppTInfo)	\
    ( (This)->lpVtbl -> GetTypeInfo(This,iTInfo,lcid,ppTInfo) ) 

#define IHelloWorldBHO_GetIDsOfNames(This,riid,rgszNames,cNames,lcid,rgDispId)	\
    ( (This)->lpVtbl -> GetIDsOfNames(This,riid,rgszNames,cNames,lcid,rgDispId) ) 

#define IHelloWorldBHO_Invoke(This,dispIdMember,riid,lcid,wFlags,pDispParams,pVarResult,pExcepInfo,puArgErr)	\
    ( (This)->lpVtbl -> Invoke(This,dispIdMember,riid,lcid,wFlags,pDispParams,pVarResult,pExcepInfo,puArgErr) ) 


#endif /* COBJMACROS */


#endif 	/* C style interface */




#endif 	/* __IHelloWorldBHO_INTERFACE_DEFINED__ */



#ifndef __HelloWorldLib_LIBRARY_DEFINED__
#define __HelloWorldLib_LIBRARY_DEFINED__

/* library HelloWorldLib */
/* [version][uuid] */ 


EXTERN_C const IID LIBID_HelloWorldLib;

EXTERN_C const CLSID CLSID_HelloWorldBHO;

#ifdef __cplusplus

class DECLSPEC_UUID("FD574140-1377-453D-8E6E-374B86CECA67")
HelloWorldBHO;
#endif
#endif /* __HelloWorldLib_LIBRARY_DEFINED__ */

/* Additional Prototypes for ALL interfaces */

/* end of Additional Prototypes */

#ifdef __cplusplus
}
#endif

#endif


