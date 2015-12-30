package test.appmsgbridge;

import java.text.Normalizer;
import java.text.Normalizer.Form;
import java.util.UUID;
import test.appmsgbridge.R;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.net.wifi.WifiManager;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.text.format.Formatter;
import android.util.Log;
import android.view.Menu;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;

@SuppressLint("NewApi")
public class MainActivity extends Activity {

	final static String TAG="AppMsgBridge";

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_main);

		DebugRcvr d = new DebugRcvr();
		registerReceiver(d, new IntentFilter("com.getpebble.action.app.SEND"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.app.ACK"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.app.NACK"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.app.RECEIVE_ACK"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.app.RECEIVE_NACK"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.ACK"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.NACK"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.app.START"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.app.STOP"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.app.CONFIGURE"));
		registerReceiver(d, new IntentFilter("com.getpebble.action.app.RECEIVE"));

		WifiManager wm = (WifiManager) getSystemService(WIFI_SERVICE);
		String ip = Formatter.formatIpAddress(wm.getConnectionInfo().getIpAddress());


		TextView wsedit = (TextView)findViewById(R.id.textView2);
		wsedit.setText("Connect to: ws://"+ip+":9011");

		sendStartBridge(null);
	}

	public void sendStartBridge(View view) {

		String wsuri="9011";

		Intent startIntent = new Intent(MainActivity.this, ForegroundService.class);
		startIntent.setAction(Constants.ACTION.STARTFOREGROUND_ACTION);
		startIntent.putExtra("wsuri", wsuri);
		startService(startIntent);
	}

	public void sendStopBridge(View view) {

		Intent startIntent = new Intent(MainActivity.this, ForegroundService.class);
		startIntent.setAction(Constants.ACTION.STOPFOREGROUND_ACTION);
		startService(startIntent);
	}

	public void sendClose(View view) {

		Intent startIntent = new Intent(MainActivity.this, ForegroundService.class);
		startIntent.setAction(Constants.ACTION.CLOSEFOREGROUND_ACTION);
		startService(startIntent);
	}



}
