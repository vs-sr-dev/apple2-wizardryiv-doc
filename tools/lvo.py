"""Histogram the  jsr d(a6)  offsets in a hunk file's code, and name them.

A negative displacement off A6 is an Amiga library vector.  The same offset
means different things in different libraries, so every offset is printed
with every library that defines one there; where the disc only opens one
library that defines it, the reading is unambiguous.  That is enough to
answer the two questions of checklist section 4 -- how much OS is being
used, and which of the five CD32 modules are actually called.

Usage: lvo.py <hunkfile>
"""
import sys, struct, collections
from hunk import parse

EXEC = {
    -30: 'Supervisor', -60: 'InitCode', -66: 'InitStruct', -72: 'MakeLibrary',
    -78: 'MakeFunctions', -84: 'FindResident', -90: 'InitResident',
    -96: 'Alert', -102: 'Debug', -108: 'Disable', -114: 'Enable',
    -120: 'Forbid', -126: 'Permit', -132: 'SetSR', -138: 'SuperState',
    -144: 'UserState', -150: 'SetIntVector', -156: 'AddIntServer',
    -162: 'RemIntServer', -168: 'Cause', -174: 'Allocate', -180: 'Deallocate',
    -186: 'AllocMem', -192: 'AllocAbs', -198: 'FreeMem', -204: 'AvailMem',
    -210: 'AllocEntry', -216: 'FreeEntry', -222: 'Insert', -228: 'AddHead',
    -234: 'AddTail', -240: 'Remove', -246: 'RemHead', -252: 'RemTail',
    -258: 'Enqueue', -264: 'FindName', -270: 'AddTask', -276: 'RemTask',
    -282: 'FindTask', -288: 'SetTaskPri', -294: 'SetSignal', -300: 'SetExcept',
    -306: 'Wait', -312: 'Signal', -318: 'AllocSignal', -324: 'FreeSignal',
    -330: 'AllocTrap', -336: 'FreeTrap', -342: 'AddPort', -348: 'RemPort',
    -354: 'PutMsg', -360: 'GetMsg', -366: 'ReplyMsg', -372: 'WaitPort',
    -378: 'FindPort', -384: 'AddLibrary', -390: 'RemLibrary',
    -396: 'OldOpenLibrary', -402: 'CloseLibrary', -408: 'SetFunction',
    -414: 'SumLibrary', -420: 'AddDevice', -426: 'RemDevice',
    -432: 'OpenDevice', -438: 'CloseDevice', -444: 'DoIO', -450: 'SendIO',
    -456: 'CheckIO', -462: 'WaitIO', -468: 'AbortIO', -474: 'AddResource',
    -480: 'RemResource', -486: 'OpenResource', -516: 'RawDoFmt',
    -522: 'GetCC', -528: 'TypeOfMem', -534: 'Procure', -540: 'Vacate',
    -552: 'OpenLibrary', -558: 'InitSemaphore', -564: 'ObtainSemaphore',
    -570: 'ReleaseSemaphore', -576: 'AttemptSemaphore',
    -600: 'AddSemaphore', -606: 'RemSemaphore', -612: 'SumKickData',
    -618: 'AddMemList', -624: 'CopyMem', -630: 'CopyMemQuick',
    -636: 'CacheClearU', -642: 'CacheClearE', -648: 'CacheControl',
    -654: 'CreateIORequest', -660: 'DeleteIORequest', -666: 'CreateMsgPort',
    -672: 'DeleteMsgPort', -678: 'ObtainSemaphoreShared',
    -684: 'AllocVec', -690: 'FreeVec', -696: 'CreatePool',
    -702: 'DeletePool', -708: 'AllocPooled', -714: 'FreePooled',
    -720: 'AttemptSemaphoreShared', -726: 'ColdReboot',
    -732: 'StackSwap', -750: 'CachePreDMA', -756: 'CachePostDMA',
}
DOS = {
    -30: 'Open', -36: 'Close', -42: 'Read', -48: 'Write', -54: 'Input',
    -60: 'Output', -66: 'Seek', -72: 'DeleteFile', -78: 'Rename',
    -84: 'Lock', -90: 'UnLock', -96: 'DupLock', -102: 'Examine',
    -108: 'ExNext', -114: 'Info', -120: 'CreateDir', -126: 'CurrentDir',
    -132: 'IoErr', -138: 'CreateProc', -144: 'Exit', -150: 'LoadSeg',
    -156: 'UnLoadSeg', -174: 'DeviceProc', -180: 'SetComment',
    -186: 'SetProtection', -192: 'DateStamp', -198: 'Delay',
    -204: 'WaitForChar', -210: 'ParentDir', -216: 'IsInteractive',
    -222: 'Execute', -228: 'AllocDosObject', -234: 'FreeDosObject',
    -246: 'DoPkt', -288: 'SetFileSize', -300: 'ReadArgs', -306: 'FindArg',
    -318: 'FreeArgs', -324: 'FilePart', -330: 'PathPart', -336: 'AddPart',
    -342: 'StartNotify', -348: 'EndNotify', -354: 'SetVar', -360: 'GetVar',
    -366: 'DeleteVar', -372: 'FindVar', -390: 'Cli', -396: 'CreateNewProc',
    -402: 'RunCommand', -408: 'GetConsoleTask', -420: 'GetFileSysTask',
    -432: 'GetArgStr', -438: 'SetArgStr', -444: 'FindCliProc',
    -450: 'MaxCli', -462: 'SetCurrentDirName', -468: 'GetCurrentDirName',
    -474: 'SetProgramName', -480: 'GetProgramName', -486: 'SetPrompt',
    -492: 'GetPrompt', -498: 'SetProgramDir', -504: 'GetProgramDir',
    -522: 'PrintFault', -528: 'ErrorReport', -540: 'Cli2',
    -558: 'PutStr', -564: 'VPrintf', -576: 'ReadItem', -582: 'StrToLong',
    -588: 'MatchFirst', -594: 'MatchNext', -600: 'MatchEnd',
    -606: 'ParsePattern', -612: 'MatchPattern', -624: 'ParsePatternNoCase',
    -630: 'MatchPatternNoCase', -642: 'SameLock', -648: 'SetMode',
    -654: 'ExAll', -696: 'AddBuffers', -702: 'CompareDates',
    -744: 'Format', -750: 'Relabel', -756: 'Inhibit',
    -798: 'NameFromLock', -804: 'NameFromFH', -810: 'SplitName',
    -822: 'Fault',
}
GFX = {
    -30: 'BltBitMap', -36: 'BltTemplate', -42: 'ClearEOL',
    -48: 'ClearScreen', -54: 'TextLength', -60: 'Text', -66: 'SetFont',
    -72: 'OpenFont', -78: 'CloseFont', -84: 'AskSoftStyle',
    -90: 'SetSoftStyle', -96: 'AddBob', -102: 'AddVSprite',
    -108: 'DoCollision', -114: 'DrawGList', -120: 'InitGels',
    -126: 'InitMasks', -132: 'RemIBob', -138: 'RemVSprite',
    -144: 'SetCollision', -150: 'SortGList', -156: 'AddAnimOb',
    -162: 'Animate', -168: 'GetGBuffers', -174: 'InitGMasks',
    -180: 'DrawEllipse', -186: 'AreaEllipse', -192: 'LoadRGB4',
    -198: 'InitRastPort', -204: 'InitVPort', -210: 'MrgCop',
    -216: 'MakeVPort', -222: 'LoadView', -228: 'WaitBlit', -234: 'SetRast',
    -240: 'Move', -246: 'Draw', -252: 'AreaMove', -258: 'AreaDraw',
    -264: 'AreaEnd', -270: 'WaitTOF', -276: 'QBlit', -282: 'InitArea',
    -288: 'SetRGB4', -294: 'QBSBlit', -300: 'BltClear', -306: 'RectFill',
    -312: 'BltPattern', -318: 'ReadPixel', -324: 'WritePixel',
    -330: 'Flood', -336: 'PolyDraw', -342: 'SetAPen', -348: 'SetBPen',
    -354: 'SetOPen', -360: 'SetDrMd', -366: 'InitView', -372: 'CBump',
    -378: 'CMove', -384: 'CWait', -390: 'VBeamPos', -396: 'InitBitMap',
    -402: 'ScrollRaster', -408: 'WaitBOVP', -414: 'GetSprite',
    -420: 'FreeSprite', -426: 'ChangeSprite', -432: 'MoveSprite',
    -438: 'LockLayerRom', -444: 'UnlockLayerRom', -450: 'SyncSBitMap',
    -456: 'CopySBitMap', -462: 'OwnBlitter', -468: 'DisownBlitter',
    -474: 'InitTmpRas', -480: 'AllocRaster', -486: 'FreeRaster',
    -492: 'AndRectRegion', -498: 'OrRectRegion', -504: 'NewRegion',
    -510: 'ClearRectRegion', -516: 'ClearRegion', -522: 'DisposeRegion',
    -528: 'FreeVPortCopLists', -534: 'FreeCopList', -540: 'ClipBlit',
    -546: 'XorRectRegion', -552: 'FreeCprList', -558: 'GetColorMap',
    -564: 'FreeColorMap', -570: 'GetRGB4', -576: 'ScrollVPort',
    -582: 'UCopperListInit', -588: 'FreeGBuffers',
    -594: 'BltBitMapRastPort', -600: 'OrRegion', -606: 'XorRegion',
    -612: 'AndRegion', -618: 'SetRGB4CM', -624: 'BltMaskBitMapRastPort',
    -636: 'AttemptLockLayerRom', -642: 'GfxNew', -648: 'GfxFree',
    -654: 'GfxAssociate', -660: 'BitMapScale', -666: 'ScalerDiv',
    -672: 'TextExtent', -678: 'TextFit', -684: 'GfxLookUp',
    -690: 'VideoControl', -696: 'OpenMonitor', -702: 'CloseMonitor',
    -708: 'FindDisplayInfo', -714: 'NextDisplayInfo',
    -732: 'GetDisplayInfoData', -738: 'FontExtent', -744: 'ReadPixelLine8',
    -750: 'WritePixelLine8', -756: 'ReadPixelArray8',
    -762: 'WritePixelArray8', -768: 'GetVPModeID',
    -774: 'ModeNotAvailable', -780: 'WeighTAMatch', -786: 'EraseRect',
    -792: 'ExtendFont', -798: 'StripFont', -804: 'CalcIVG',
    -810: 'AttachPalExtra', -816: 'ObtainBestPenA', -828: 'SetRGB32',
    -834: 'GetAPen', -840: 'GetBPen', -846: 'GetDrMd',
    -852: 'GetOutlinePen', -858: 'LoadRGB32', -864: 'SetChipRev',
    -870: 'SetABPenDrMd', -876: 'GetRPAttrsA', -882: 'SetRPAttrsA',
    -888: 'BestModeIDA'
}
INT = {
    -30: 'OpenIntuition', -36: 'Intuition', -42: 'AddGadget',
    -48: 'ClearDMRequest', -54: 'ClearMenuStrip', -60: 'ClearPointer',
    -66: 'CloseScreen', -72: 'CloseWindow', -78: 'CloseWorkBench',
    -84: 'CurrentTime', -90: 'DisplayAlert', -96: 'DisplayBeep',
    -102: 'DoubleClick', -108: 'DrawBorder', -114: 'DrawImage',
    -120: 'EndRequest', -126: 'GetDefPrefs', -132: 'GetPrefs',
    -138: 'InitRequester', -144: 'ItemAddress', -150: 'ModifyIDCMP',
    -156: 'ModifyProp', -162: 'MoveScreen', -168: 'MoveWindow',
    -174: 'OffGadget', -180: 'OffMenu', -186: 'OnGadget', -192: 'OnMenu',
    -198: 'OpenIntuition2', -204: 'OpenScreen', -210: 'OpenWindow',
    -216: 'OpenWorkBench', -222: 'PrintIText', -228: 'RefreshGadgets',
    -234: 'RemoveGadget', -240: 'ReportMouse', -246: 'Request',
    -252: 'ScreenToBack', -258: 'ScreenToFront', -264: 'SetDMRequest',
    -270: 'SetMenuStrip', -276: 'SetPointer', -282: 'SetWindowTitles',
    -288: 'ShowTitle', -294: 'SizeWindow', -300: 'ViewAddress',
    -306: 'ViewPortAddress', -312: 'WindowLimits', -318: 'WindowToBack',
    -324: 'WindowToFront', -330: 'WBenchToBack', -336: 'WBenchToFront',
    -342: 'AutoRequest', -348: 'BeginRefresh', -354: 'BuildSysRequest',
    -360: 'EndRefresh', -366: 'FreeSysRequest', -372: 'MakeScreen',
    -378: 'RemakeDisplay', -384: 'RethinkDisplay', -390: 'AllocRemember',
    -396: 'AlohaWorkbench', -402: 'FreeRemember', -408: 'LockIBase',
    -414: 'UnlockIBase', -420: 'GetScreenData', -426: 'RefreshGList',
    -432: 'AddGList', -438: 'RemoveGList', -444: 'ActivateWindow',
    -450: 'RefreshWindowFrame', -456: 'ActivateGadget',
    -462: 'NewModifyProp', -468: 'QueryOverscan',
    -474: 'MoveWindowInFrontOf', -480: 'ChangeWindowBox',
    -486: 'SetEditHook', -492: 'SetMouseQueue', -498: 'ZipWindow',
    -504: 'LockPubScreen', -510: 'UnlockPubScreen',
    -516: 'LockPubScreenList', -522: 'UnlockPubScreenList',
    -528: 'NextPubScreen', -534: 'SetDefaultPubScreen',
    -540: 'SetPubScreenModes', -546: 'PubScreenStatus',
    -552: 'ObtainGIRPort', -558: 'ReleaseGIRPort', -564: 'GadgetMouse',
    -570: 'reserved', -576: 'GetDefaultPubScreen', -582: 'EasyRequestArgs',
    -588: 'BuildEasyRequestArgs', -594: 'SysReqHandler',
    -600: 'OpenWindowTagList', -606: 'OpenScreenTagList',
    -612: 'DrawImageState', -618: 'PointInImage', -624: 'EraseImage',
    -630: 'NewObjectA', -636: 'DisposeObject', -642: 'SetAttrsA',
    -648: 'GetAttr', -654: 'SetGadgetAttrsA', -660: 'NextObject',
    -666: 'FindClass', -672: 'MakeClass', -678: 'AddClass',
    -684: 'RemoveClass', -690: 'FreeClass'
}
LOWLEVEL = {
    -30: 'ReadJoyPort', -36: 'GetLanguageSelection', -42: 'GetKey',
    -48: 'QueryKeys', -54: 'AddKBInt', -60: 'RemKBInt',
    -66: 'SystemControlA', -72: 'AddTimerInt', -78: 'RemTimerInt',
    -84: 'StopTimerInt', -90: 'StartTimerInt', -96: 'ElapsedTime',
    -102: 'AddVBlankInt', -108: 'RemVBlankInt', -114: 'SetJoyPortAttrsA',
}
NONVOL = {
    -30: 'ReadNVData', -36: 'WriteNVData', -42: 'FreeNVData',
    -48: 'GetCopyNVList', -54: 'FreeNVList', -60: 'DeleteNVData',
    -66: 'SetNVProtection',
}
LIBS = [('exec', EXEC), ('dos', DOS), ('gfx', GFX), ('intuition', INT),
        ('lowlevel', LOWLEVEL), ('nonvolatile', NONVOL)]


def histogram(body, only=None):
    h = collections.Counter()
    for op in (b'\x4e\xae', b'\x4e\xee'):
        i = 0
        while True:
            i = body.find(op, i)
            if i < 0 or i + 4 > len(body):
                break
            v = struct.unpack_from('>h', body, i + 2)[0]
            if -1200 < v < 0:
                h[v] += 1
            i += 2
    return h


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    h = parse(d)
    body = b''.join(d[k['off']:k['off'] + k['size']] for k in h['hunks']
                    if k['size'])
    hist = histogram(body)
    print('%s: %d calls through a6, %d distinct offsets'
          % (sys.argv[1], sum(hist.values()), len(hist)))
    for off in sorted(hist):
        names = ['%s:%s' % (n, t[off]) for n, t in LIBS if off in t]
        print('  %5d(a6)  x%-4d %s' % (off, hist[off], '  '.join(names)))
