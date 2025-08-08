import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'screens/survey_screen.dart';
import 'services/storage_service.dart';
import 'services/sync_service.dart';

void main() {
  runApp(BharatPulseApp());
}

class BharatPulseApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<StorageService>(create: (_) => StorageService()),
        Provider<SyncService>(create: (_) => SyncService()),
      ],
      child: MaterialApp(
        title: 'BharatPulse',
        theme: ThemeData(
          primarySwatch: Colors.green,
          fontFamily: 'Noto Sans',
          textTheme: TextTheme(
            // Large, readable fonts for rural users
            bodyLarge: TextStyle(fontSize: 18),
            bodyMedium: TextStyle(fontSize: 16),
            headlineLarge: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
          ),
        ),
        home: SurveyScreen(),
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}
