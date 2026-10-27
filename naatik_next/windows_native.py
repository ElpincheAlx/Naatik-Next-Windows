"""Owned Windows process trees with JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE."""
import ctypes as C
from ctypes import wintypes as W

class BasicLimits(C.Structure):
    _fields_ = [('PerProcessUserTimeLimit', C.c_int64), ('PerJobUserTimeLimit', C.c_int64),
                ('LimitFlags', W.DWORD), ('MinimumWorkingSetSize', C.c_size_t),
                ('MaximumWorkingSetSize', C.c_size_t), ('ActiveProcessLimit', W.DWORD),
                ('Affinity', C.c_size_t), ('PriorityClass', W.DWORD), ('SchedulingClass', W.DWORD)]
class IO(C.Structure):
    _fields_ = [(name,C.c_uint64) for name in ('ReadOperationCount','WriteOperationCount','OtherOperationCount',
                                             'ReadTransferCount','WriteTransferCount','OtherTransferCount')]
class ExtendedLimits(C.Structure):
    _fields_ = [('BasicLimitInformation',BasicLimits), ('IoInfo',IO),
                ('ProcessMemoryLimit',C.c_size_t), ('JobMemoryLimit',C.c_size_t),
                ('PeakProcessMemoryUsed',C.c_size_t), ('PeakJobMemoryUsed',C.c_size_t)]

class Job:
    def __init__(self, pid):
        self.handle = None
        self.api = C.WinDLL('kernel32', use_last_error=True)
        for name, restype, args in (
            ('CreateJobObjectW',W.HANDLE,[C.c_void_p,W.LPCWSTR]),
            ('SetInformationJobObject',W.BOOL,[W.HANDLE,C.c_int,C.c_void_p,W.DWORD]),
            ('OpenProcess',W.HANDLE,[W.DWORD,W.BOOL,W.DWORD]),
            ('AssignProcessToJobObject',W.BOOL,[W.HANDLE,W.HANDLE]),
            ('CloseHandle',W.BOOL,[W.HANDLE])):
            fn=getattr(self.api,name); fn.restype=restype; fn.argtypes=args
        self.handle = self.api.CreateJobObjectW(None,None)
        if not self.handle: raise C.WinError(C.get_last_error())
        process = None
        try:
            limits=ExtendedLimits(); limits.BasicLimitInformation.LimitFlags=0x2000
            if not self.api.SetInformationJobObject(self.handle,9,C.byref(limits),C.sizeof(limits)):
                raise C.WinError(C.get_last_error())
            process=self.api.OpenProcess(0x0100 | 0x0001,False,pid)  # SET_QUOTA | TERMINATE
            if not process or not self.api.AssignProcessToJobObject(self.handle,process):
                raise C.WinError(C.get_last_error())
        except BaseException:
            self.close(); raise
        finally:
            if process: self.api.CloseHandle(process)
    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle=None
