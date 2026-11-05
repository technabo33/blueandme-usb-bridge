import unittest,sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'wheel'))
from avrcp import choose_player, available_players, send, AVRCPError, player_address

P='/org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF/player0'
class TestAVRCP(unittest.TestCase):
    def test_player_address(self):
        self.assertEqual(player_address(P),'AA:BB:CC:DD:EE:FF')

    def test_only_trusted(self):
        def mock(args,timeout):
            if args[0]=='bluetoothctl':return SimpleNamespace(returncode=0,stdout='Paired: yes\nTrusted: no\nConnected: yes')
            return SimpleNamespace(returncode=0,stdout='')
        with self.assertRaises(AVRCPError): choose_player([P],runner=mock)

    def test_no_player(self):
        with self.assertRaises(AVRCPError): choose_player([])

    def test_status_tree(self):
        def mock(args,timeout):
            return SimpleNamespace(returncode=0,stdout='└─'+P)
        self.assertEqual(available_players(mock),[P])

    def test_manual_next(self):
        calls=[]
        def mock(args,timeout):
            calls.append(args)
            if args[0]=='busctl' and 'tree' in args:return SimpleNamespace(returncode=0,stdout=P)
            if args[0]=='bluetoothctl':return SimpleNamespace(returncode=0,stdout='Paired: yes\nTrusted: yes\nConnected: yes')
            return SimpleNamespace(returncode=0,stdout='')
        send('next',runner=mock,log=Path('/does/not/exist'))
        self.assertEqual(calls[-1][-1],'Next')

    def test_bad_command(self):
        with self.assertRaises(AVRCPError): send('rewind')

if __name__=='__main__':unittest.main()
