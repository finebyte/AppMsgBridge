package test.appmsgbridge;

public class Constants {
	public interface ACTION {
		public static String MAIN_ACTION = "test.appmsgbridge.action.main";
		public static String SENDWS = "test.appmsgbridge.action.sendws";
		public static String PLAY_ACTION = "test.appmsgbridge.action.play";
		public static String NEXT_ACTION = "test.appmsgbridge.action.next";
		public static String STARTFOREGROUND_ACTION = "test.appmsgbridge.action.startforeground";
		public static String STOPFOREGROUND_ACTION = "test.appmsgbridge.action.stopforeground";
	}

	public interface NOTIFICATION_ID {
		public static int FOREGROUND_SERVICE = 101;
	}
}