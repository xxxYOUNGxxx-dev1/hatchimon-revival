package com.zettabridge.launcher;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.*;

/** Personal launcher for the bundled game; translator implementation is upstream. */
public final class HatchimonLaunchActivity extends Activity {
    private static final String GAME="com.hyunmoo.hatchimon.farm.dev";
    private static final String VERSION="1.13-dev5";
    private TextView status;
    private Button start;
    private volatile boolean busy;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        setTitle("Merge Hatchimon Dev");
        LinearLayout body=new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        int p=(int)(24*getResources().getDisplayMetrics().density);
        body.setPadding(p,p,p,p);
        TextView title=new TextView(this);
        title.setText("Merge Hatchimon · ARM64"); title.setTextSize(24); body.addView(title);
        TextView info=new TextView(this);
        info.setText("Экспериментальная версия на ZettaBridge 0.1.0.\n\nВ игре: DEV → сумма до 1 миллиарда; уровень хачимона 1–72, включая светящиеся 37–72.\n\nПервый запуск может занять время. Сохранения хранятся отдельно от прежней установки.");
        body.addView(info);
        status=new TextView(this); body.addView(status);
        start=new Button(this); start.setText("Запустить игру"); body.addView(start);
        start.setOnClickListener(new View.OnClickListener() { public void onClick(View v) { launch(); }});
        Button diagnostics=new Button(this); diagnostics.setText("Диагностика ZettaBridge"); body.addView(diagnostics);
        diagnostics.setOnClickListener(new View.OnClickListener() { public void onClick(View v) {
            startActivity(new Intent().setClassName(getPackageName(),"com.zettabridge.launcher.LibraryActivity"));
        }});
        setContentView(body);
    }

    private void launch() {
        if(busy) return;
        busy=true;start.setEnabled(false);status.setText("Подготовка игры…");
        new Thread(new Runnable() { public void run() {
            try {
                PluginRecord game=null;
                for(PluginRecord item:PluginStore.list(HatchimonLaunchActivity.this)) {
                    if(GAME.equals(item.packageName) && VERSION.equals(item.versionName)) {game=item;break;}
                }
                if(game==null) {
                    File temp=File.createTempFile("hatchimon-",".apk",getCacheDir());
                    try {
                        try(InputStream in=getAssets().open("bundled/plugin.apk");OutputStream out=new FileOutputStream(temp)) {
                            byte[] buffer=new byte[65536];int n;
                            while((n=in.read(buffer))!=-1) out.write(buffer,0,n);
                        }
                        game=PluginStore.importApk(HatchimonLaunchActivity.this,Uri.fromFile(temp));
                    } finally {temp.delete();}
                    game.hideAds=false;game.diagnostics=true;game.save();
                }
                if(!game.isLaunchable()) throw new IOException(game.status());
                final String name=game.packageName;
                runOnUiThread(new Runnable() { public void run() {
                    busy=false;start.setEnabled(true);status.setText("Запуск…");
                    try {startActivity(PluginSwitchActivity.intent(HatchimonLaunchActivity.this,name));}
                    catch(RuntimeException error) {status.setText("Не удалось запустить игру: "+error.toString());}
                }});
            } catch(final Exception error) {
                android.util.Log.e("hatchimon-wrapper","Cannot prepare bundled game",error);
                runOnUiThread(new Runnable() { public void run() {
                    busy=false;start.setEnabled(true);status.setText("Не удалось подготовить игру: "+error.toString());
                }});
            }
        }},"hatchimon-import").start();
    }
}
