import 'dart:convert';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class StorageService {
  static Database? _database;
  
  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB();
    return _database!;
  }
  
  Future<Database> _initDB() async {
    String path = join(await getDatabasesPath(), 'bharatpulse.db');
    
    return await openDatabase(
      path,
      version: 1,
      onCreate: _onCreate,
    );
  }
  
  Future _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE survey_responses (
        id TEXT PRIMARY KEY,
        survey_id TEXT NOT NULL,
        respondent_id TEXT,
        responses TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        synced INTEGER DEFAULT 0,
        location_lat REAL,
        location_lng REAL,
        device_info TEXT
      )
    ''');
    
    await db.execute('''
      CREATE TABLE survey_definitions (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        definition TEXT NOT NULL,
        version INTEGER DEFAULT 1,
        downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    ''');
    
    await db.execute('''
      CREATE TABLE audio_cache (
        id TEXT PRIMARY KEY,
        audio_data BLOB,
        transcription TEXT,
        confidence REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    ''');
  }
  
  Future<void> saveResponse(SurveyResponse response) async {
    final db = await database;
    
    await db.insert(
      'survey_responses',
      {
        'id': response.id,
        'survey_id': response.surveyId,
        'respondent_id': response.respondentId,
        'responses': jsonEncode(response.responses),
        'synced': 0,
        'location_lat': response.location?.latitude,
        'location_lng': response.location?.longitude,
        'device_info': jsonEncode(response.deviceInfo),
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }
  
  Future<List<SurveyResponse>> getUnsyncedResponses() async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'survey_responses',
      where: 'synced = ?',
      whereArgs: [0],
    );
    
    return List.generate(maps.length, (i) {
      return SurveyResponse.fromMap(maps[i]);
    });
  }
  Future<List<Map<String, dynamic>>> getAllResponses() async {
  final db = await database;
  return await db.query('responses');
}
  
  Future<void> markSynced(String responseId) async {
    final db = await database;
    await db.update(
      'survey_responses',
      {'synced': 1},
      where: 'id = ?',
      whereArgs: [responseId],
    );
  }
}

class SurveyResponse {
  final String id;
  final String surveyId;
  final String? respondentId;
  final Map<String, dynamic> responses;
  final DateTime createdAt;
  final bool synced;
  final LocationData? location;
  final Map<String, dynamic>? deviceInfo;

  SurveyResponse({
    required this.id,
    required this.surveyId,
    this.respondentId,
    required this.responses,
    required this.createdAt,
    required this.synced,
    this.location,
    this.deviceInfo,
  });

  static SurveyResponse fromMap(Map<String, dynamic> map) {
    return SurveyResponse(
      id: map['id'],
      surveyId: map['survey_id'],
      respondentId: map['respondent_id'],
      responses: jsonDecode(map['responses']),
      createdAt: DateTime.parse(map['created_at']),
      synced: map['synced'] == 1,
      location: map['location_lat'] != null ? LocationData(
        latitude: map['location_lat'],
        longitude: map['location_lng'],
      ) : null,
      deviceInfo: map['device_info'] != null ? 
        jsonDecode(map['device_info']) : null,
    );
  }
}

class LocationData {
  final double latitude;
  final double longitude;

  LocationData({required this.latitude, required this.longitude});
}
