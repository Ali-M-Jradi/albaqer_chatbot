// =====================================================
// Flutter Service to Call AlBaqer Chatbot API
// Place this in: lib/services/chatbot_service.dart
// =====================================================

import 'dart:convert';
import 'package:http/http.dart' as http;

class ChatbotService {
  // ⚠️ IMPORTANT: Update this to your server's IP address
  // For local testing: Use your computer's local IP (e.g., 192.168.1.100)
  // For production: Use your server's public IP or domain
  static const String baseUrl = 'http://YOUR_SERVER_IP:8000/api';
  
  // To find your IP on Windows: Open CMD and type "ipconfig"
  // Look for "IPv4 Address" under your network adapter
  // Example: static const String baseUrl = 'http://192.168.1.100:8000/api';
  
  /// Send a chat message to the chatbot
  /// 
  /// Returns a Map containing:
  /// - session_id: Unique conversation identifier
  /// - message: Bot's response
  /// - routed_to: Which agent handled the query
  /// - sources: List of knowledge base sources used (optional)
  static Future<Map<String, dynamic>> sendMessage({
    required String message,
    int? userId,
    String? sessionId,
    Map<String, dynamic>? metadata,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/chat'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'message': message,
          'user_id': userId,
          'session_id': sessionId,
          'metadata': metadata ?? {},
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to send message: ${response.statusCode} - ${response.body}');
      }
    } catch (e) {
      print('Error sending message: $e');
      rethrow;
    }
  }
  
  /// Get chat history for a specific user
  /// 
  /// Returns a List of conversations, each containing:
  /// - conversation_id: Database ID
  /// - session_id: Unique session identifier
  /// - messages: List of all messages in the conversation
  /// - created_at: When conversation started
  /// - last_message_at: Most recent message timestamp
  static Future<List<dynamic>> getChatHistory({
    required int userId,
    int limit = 10,
  }) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/chat/history/$userId?limit=$limit'),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to load history: ${response.statusCode}');
      }
    } catch (e) {
      print('Error loading history: $e');
      rethrow;
    }
  }
  
  /// Get a specific conversation by session ID
  static Future<Map<String, dynamic>> getConversation({
    required String sessionId,
  }) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/chat/session/$sessionId'),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else if (response.statusCode == 404) {
        throw Exception('Conversation not found');
      } else {
        throw Exception('Failed to load conversation: ${response.statusCode}');
      }
    } catch (e) {
      print('Error loading conversation: $e');
      rethrow;
    }
  }
  
  /// Delete a conversation by session ID
  static Future<void> deleteConversation({
    required String sessionId,
  }) async {
    try {
      final response = await http.delete(
        Uri.parse('$baseUrl/chat/history/$sessionId'),
      );
      
      if (response.statusCode == 200) {
        print('Conversation deleted successfully');
      } else if (response.statusCode == 404) {
        throw Exception('Conversation not found');
      } else {
        throw Exception('Failed to delete conversation: ${response.statusCode}');
      }
    } catch (e) {
      print('Error deleting conversation: $e');
      rethrow;
    }
  }
  
  /// Check if the chatbot API is healthy
  static Future<bool> checkHealth() async {
    try {
      final response = await http.get(
        Uri.parse('${baseUrl.replaceAll('/api', '')}/api/health'),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['status'] == 'healthy';
      }
      return false;
    } catch (e) {
      print('Health check failed: $e');
      return false;
    }
  }
}


// =====================================================
// EXAMPLE USAGE IN A FLUTTER WIDGET
// =====================================================

/*
import 'package:flutter/material.dart';
import 'services/chatbot_service.dart';

class ChatScreen extends StatefulWidget {
  final int userId;
  
  const ChatScreen({Key? key, required this.userId}) : super(key: key);
  
  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final List<Map<String, dynamic>> _messages = [];
  String? _sessionId;
  bool _isLoading = false;
  
  @override
  void initState() {
    super.initState();
    _loadChatHistory();
  }
  
  Future<void> _loadChatHistory() async {
    try {
      final history = await ChatbotService.getChatHistory(
        userId: widget.userId,
        limit: 1,
      );
      
      if (history.isNotEmpty) {
        final lastConversation = history.first;
        setState(() {
          _sessionId = lastConversation['session_id'];
          _messages.addAll(
            List<Map<String, dynamic>>.from(lastConversation['messages'])
          );
        });
      }
    } catch (e) {
      print('Error loading history: $e');
    }
  }
  
  Future<void> _sendMessage() async {
    final message = _messageController.text.trim();
    if (message.isEmpty) return;
    
    setState(() {
      _messages.add({'role': 'user', 'content': message});
      _isLoading = true;
    });
    
    _messageController.clear();
    
    try {
      final response = await ChatbotService.sendMessage(
        message: message,
        userId: widget.userId,
        sessionId: _sessionId,
      );
      
      setState(() {
        _sessionId = response['session_id'];
        _messages.add({
          'role': 'assistant',
          'content': response['message'],
          'routed_to': response['routed_to'],
        });
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _messages.add({
          'role': 'error',
          'content': 'Failed to send message: $e',
        });
        _isLoading = false;
      });
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AlBaqer Chatbot'),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                final isUser = msg['role'] == 'user';
                
                return Align(
                  alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.all(8),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: isUser ? Colors.blue : Colors.grey[300],
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      msg['content'],
                      style: TextStyle(
                        color: isUser ? Colors.white : Colors.black,
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.all(8.0),
              child: CircularProgressIndicator(),
            ),
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    decoration: const InputDecoration(
                      hintText: 'Ask me anything...',
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.send),
                  onPressed: _sendMessage,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
*/
