import 'dart:convert';
import 'package:http/http.dart' as http;
import 'storage_service.dart';
import 'package:connectivity_plus/connectivity_plus.dart';

class SyncService {
  final String baseUrl = 'http://your-api-url.com/api';
  final StorageService _storage = StorageService();
  
  Future<bool> syncResponses() async {
    try {
      // Check connectivity
      var connectivityResult = await Connectivity().checkConnectivity();
      if (connectivityResult == ConnectivityResult.none) {
        return false;
      }
      
      // Get unsynced responses
      List<SurveyResponse> unsyncedResponses = 
          await _storage.getUnsyncedResponses();
      
      int syncedCount = 0;
      
      for (SurveyResponse response in unsyncedResponses) {
        bool success = await _syncSingleResponse(response);
        if (success) {
          await _storage.markSynced(response.id);
          syncedCount++;
        }
      }
      
      print('Synced $syncedCount of ${unsyncedResponses.length} responses');
      return syncedCount > 0;
      
    } catch (e) {
      print('Sync error: $e');
      return false;
    }
  }
  
  Future<bool> _syncSingleResponse(SurveyResponse response) async {
    try {
      final url = Uri.parse('$baseUrl/surveys/${response.surveyId}/responses');
      
      final responseData = {
        'id': response.id,
        'survey_id': response.surveyId,
        'respondent_id': response.respondentId,
        'responses': response.responses,
        'created_at': response.createdAt.toIso8601String(),
        'location': response.location != null ? {
          'latitude': response.location!.latitude,
          'longitude': response.location!.longitude,
        } : null,
        'device_info': response.deviceInfo,
      };
      
      final httpResponse = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer YOUR_API_KEY',
        },
        body: jsonEncode(responseData),
      ).timeout(Duration(seconds: 30));
      
      return httpResponse.statusCode == 200 || httpResponse.statusCode == 201;
      
    } catch (e) {
      print('Error syncing response ${response.id}: $e');
      return false;
    }
  }
  
  Future<void> exportToCSV() async {
    // Implementation for CSV export
    List<SurveyResponse> allResponses = await _storage.getAllResponses();
    
    List<List<dynamic>> csvData = [];
    
    // Add headers
    csvData.add([
      'Response ID',
      'Survey ID',
      'Respondent ID',
      'Created At',
      'Age',
      'Name',
      'Location',
      'Occupation',
      'Income',
      'Synced'
    ]);
    
    // Add data rows
    for (SurveyResponse response in allResponses) {
      Map<String, dynamic> responses = response.responses;
      
      csvData.add([
        response.id,
        response.surveyId,
        response.respondentId,
        response.createdAt.toIso8601String(),
        responses['age'] ?? '',
        responses['name'] ?? '',
        responses['location'] ?? '',
        responses['occupation'] ?? '',
        responses['income'] ?? '',
        response.synced ? 'Yes' : 'No',
      ]);
    }
    
    // Convert to CSV string and save/share
    String csvString = _convertToCSV(csvData);
    
    // Save to device or share
    // Implementation depends on requirements
  }
  
  String _convertToCSV(List<List<dynamic>> data) {
    return data.map((row) => 
      row.map((cell) => '"${cell.toString().replaceAll('"', '""')}"').join(',')
    ).join('\n');
  }
}
