import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';
import * as crypto from 'crypto';

const execAsync = promisify(exec);
let decorationType: vscode.TextEditorDecorationType;

// Глобальное хранилище данных о SQL-запросах для CodeLens
interface SqlQueryInfo {
    id: number;
    query: string;
    verdict: string;
    reason: string;
    correction: string;
    start: number;
    end: number;
    start_line?: number;
    start_column?: number;
    end_line?: number;
    end_column?: number;
    line_content?: string;
    hash: string; // Уникальный хеш для идентификации запроса
    filePath: string;
}

let currentSqlQueries: Map<string, SqlQueryInfo[]> = new Map();

// Глобальное хранилище для декораций по файлам
interface FileDecorations {
    correctQueries: vscode.DecorationOptions[];
    errorQueries: vscode.DecorationOptions[];
    warningQueries: vscode.DecorationOptions[];
    unknownQueries: vscode.DecorationOptions[];
    // Типы декораций
    correctDecorationType: vscode.TextEditorDecorationType;
    errorDecorationType: vscode.TextEditorDecorationType;
    warningDecorationType: vscode.TextEditorDecorationType;
    unknownDecorationType: vscode.TextEditorDecorationType;
}

let currentDecorations: Map<string, FileDecorations> = new Map();

// CodeLens Provider для отображения кнопок над SQL-запросами
class SqlCodeLensProvider implements vscode.CodeLensProvider {
    private _onDidChangeCodeLenses: vscode.EventEmitter<void> = new vscode.EventEmitter<void>();
    public readonly onDidChangeCodeLenses: vscode.Event<void> = this._onDidChangeCodeLenses.event;

    public refresh(): void {
        this._onDidChangeCodeLenses.fire();
    }

    public provideCodeLenses(document: vscode.TextDocument, token: vscode.CancellationToken): vscode.CodeLens[] | Thenable<vscode.CodeLens[]> {
        const codeLenses: vscode.CodeLens[] = [];
        const filePath = document.fileName;
        const queries = currentSqlQueries.get(filePath);

        if (!queries) {
            return codeLenses;
        }

        for (const query of queries) {
            // Пропускаем корректные запросы без исправлений
            if (query.verdict === 'True' || !query.correction || query.correction.trim() === '' || query.correction === query.query) {
                continue;
            }

            let range: vscode.Range;
            if (query.start_line !== undefined && query.start_column !== undefined && 
                query.end_line !== undefined && query.end_column !== undefined) {
                // Используем точные позиции
                const startPos = new vscode.Position(query.start_line - 1, query.start_column);
                const endPos = new vscode.Position(query.end_line - 1, query.end_column + 1);
                range = new vscode.Range(startPos, endPos);
            } else {
                // Fallback к абсолютным позициям
                const startPos = document.positionAt(query.start);
                const endPos = document.positionAt(query.end + 1);
                range = new vscode.Range(startPos, endPos);
            }

            // Позиция для отображения CodeLens (прямо над строкой с SQL-запросом)
            const codeLensPosition = new vscode.Position(range.start.line, 0);
            const codeLensRange = new vscode.Range(codeLensPosition, codeLensPosition);

            // Отладочная информация для CodeLens
            console.log(`CodeLens для SQL запроса ${query.hash}:
                SQL: "${query.query.substring(0, 50)}..."
                SQL Range: ${range.start.line}:${range.start.character} - ${range.end.line}:${range.end.character}
                CodeLens позиция: ${codeLensPosition.line}:${codeLensPosition.character}
                Исправление: "${query.correction.substring(0, 50)}..."`);

            // Создаем кнопки для действий
            const applyCommand: vscode.Command = {
                title: `$(check) Применить исправление`,
                command: 'sqlinter.applySqlFix',
                arguments: [query.hash, filePath]
            };

            const dismissCommand: vscode.Command = {
                title: `$(close) Отклонить`,
                command: 'sqlinter.dismissSqlFix', 
                arguments: [query.hash, filePath]
            };

            // Добавляем CodeLens для каждой кнопки
            codeLenses.push(new vscode.CodeLens(codeLensRange, applyCommand));
            codeLenses.push(new vscode.CodeLens(codeLensRange, dismissCommand));
        }

        return codeLenses;
    }
}

export function activate(context: vscode.ExtensionContext) {
    const extensionRootPath = context.extensionUri.fsPath;
    console.log('Congratulations, your extension "sqlinter" is now active!');
    console.log(`путь к расширению: ${extensionRootPath}`);

    decorationType = vscode.window.createTextEditorDecorationType({
        backgroundColor: 'rgba(100, 200, 100, 0.2)',
        border: '1px solid rgba(100, 200, 100, 0.7)'
    });

    // Регистрируем CodeLens провайдер
    const codeLensProvider = new SqlCodeLensProvider();
    const codeLensProviderDisposable = vscode.languages.registerCodeLensProvider(
        { language: 'python' },
        codeLensProvider
    );
    context.subscriptions.push(codeLensProviderDisposable);
    //проверка наличия API ключа
    const config = vscode.workspace.getConfiguration('sqlinter');
    if (!config.get('openAiApiKey')) {
        vscode.window.showInformationMessage(
            'Для работы SQLinter требуется OpenAI API ключ. Запустите команду "SQLinter: Set API Key"',
            'Ввести ключ'
        ).then(selection => {
            if (selection) {
                vscode.commands.executeCommand('sqlinter.setApiKey');
            }
        });
    }

    //Получаем API ключ
    async function getOpenAIApiKey() {
        const config = vscode.workspace.getConfiguration('sqlinter');
        const apiKey = config.get<string>('openAiApiKey');
        console.log(`ApiKey: ${apiKey}`);

    if (!apiKey) {
        const action = await vscode.window.showErrorMessage(
            'OpenAI API ключ не найден', 
            'Ввести ключ'
        );
        
        if (action === 'Ввести ключ') {
            await vscode.commands.executeCommand('sqlinter.setApiKey');
        }
        return;
    }
    return apiKey;
}

    // Вынесенная функция для анализа SQL
    async function analyzeSqlInDocument(document: vscode.TextDocument) {
        const absoluteFilePath = document.fileName;
        const apiKey = await getOpenAIApiKey();
        console.log(`Обработан файл: ${absoluteFilePath}`);
        
        if (document.languageId === 'python' || document.fileName.endsWith('.py')) {
            try {
                const sqlQueries = await runPythonScript(extensionRootPath, absoluteFilePath, apiKey);
                console.log(sqlQueries);
                
                // Создаем хеши для SQL запросов и сохраняем данные
                const processedQueries: SqlQueryInfo[] = sqlQueries.map(query => ({
                    ...query,
                    hash: createSqlQueryHash(query.query, absoluteFilePath, query.start),
                    filePath: absoluteFilePath
                }));
                
                // Сохраняем данные для CodeLens
                currentSqlQueries.set(absoluteFilePath, processedQueries);
                
                await highlightSqlQueries(document, sqlQueries);
                
                // Обновляем CodeLens
                codeLensProvider.refresh();
                
                vscode.window.showInformationMessage(`Обработан файл: ${absoluteFilePath}`);
            } catch (error) {
                vscode.window.showErrorMessage(`Ошибка обработки ${absoluteFilePath}: ${error}`);
            }
        }
    }

    // Команда для установки API ключа
    const setApiKeyCommand = vscode.commands.registerCommand('sqlinter.setApiKey', async () => {
        const apiKey = await vscode.window.showInputBox({
            prompt: 'Введите ваш OpenAI API ключ',
            password: true, // Скрываем ввод
            ignoreFocusOut: true
        });

        if (apiKey) {
            // Сохраняем в глобальных настройках VS Code
            await vscode.workspace.getConfiguration('sqlinter').update(
                'openAiApiKey',
                apiKey,
                vscode.ConfigurationTarget.Global
            );
            vscode.window.showInformationMessage('API ключ успешно сохранён!')
            console.log(apiKey);
        }
    });

    const clearApiKeyCommand = vscode.commands.registerCommand('sqlinter.clearApiKey', async () => {
        await vscode.workspace.getConfiguration('sqlinter').update(
            'openAiApiKey',
            undefined,
            vscode.ConfigurationTarget.Global
        );
        vscode.window.showInformationMessage('API ключ успешно удалён!');
    });

    // Новая команда для принудительного анализа SQL
    const analyzeSqlCommand = vscode.commands.registerCommand('sqlinter.analyzeSql', async () => {
        const activeEditor = vscode.window.activeTextEditor;
        
        if (!activeEditor) {
            vscode.window.showWarningMessage('Нет активного файла для анализа');
            return;
        }

        const document = activeEditor.document;
        
        // Проверяем, что это Python файл
        if (document.languageId !== 'python' && !document.fileName.endsWith('.py')) {
            vscode.window.showWarningMessage('SQLinter работает только с Python файлами');
            return;
        }

        // Сохраняем файл перед анализом
        if (document.isDirty) {
            await document.save();
            vscode.window.showInformationMessage('Файл сохранён. Запуск анализа...');
        } else {
            vscode.window.showInformationMessage('Запуск анализа SQL...');
        }

        // Запускаем анализ
        await analyzeSqlInDocument(document);
    });

    // Команда для применения исправления SQL
    const applySqlFixCommand = vscode.commands.registerCommand('sqlinter.applySqlFix', async (queryHash: string, filePath: string) => {
        await applySqlFix(queryHash, filePath, codeLensProvider);
    });

    // Команда для отклонения исправления SQL
    const dismissSqlFixCommand = vscode.commands.registerCommand('sqlinter.dismissSqlFix', async (queryHash: string, filePath: string) => {
        await dismissSqlFix(queryHash, filePath, codeLensProvider);
    });

    //обработка сохранения
    const saveDisposable = vscode.workspace.onDidSaveTextDocument(async (document) => {
        await analyzeSqlInDocument(document);
    });

    // Добавляем в подписки для очистки при деактивации
    context.subscriptions.push(saveDisposable);
    context.subscriptions.push(setApiKeyCommand);
    context.subscriptions.push(clearApiKeyCommand);
    context.subscriptions.push(analyzeSqlCommand);
    context.subscriptions.push(applySqlFixCommand);
    context.subscriptions.push(dismissSqlFixCommand);

    //базовый хеллоу ворлд
    const disposable = vscode.commands.registerCommand('sqlinter.helloWorld', () => {
		console.log('Hello World from SQLinter!');
        vscode.window.showInformationMessage('Hello World from SQLinter!');
    });
    context.subscriptions.push(disposable);
}

async function runPythonScript(rootPath: string, filePath: string, apiKey?: string) {
    // Получаем путь к директории с расширением
    const extensionDir = rootPath;
    
    // Формируем путь к Python-скрипту в той же директории
    const pythonScriptPath = path.join(extensionDir, 'scripts/main.py'); 
    console.log(`запущен скрипт: ${pythonScriptPath}`);
    const command = `python "${pythonScriptPath}" "${filePath}" ${apiKey ? `"${apiKey}"` : ''}`;
    
    // Явно устанавливаем кодировку UTF-8 для Windows
    const execOptions = {
        encoding: 'utf-8' as BufferEncoding,
        env: { 
            ...process.env, 
            PYTHONIOENCODING: 'utf-8'  // Принудительно устанавливаем UTF-8 для Python
        }
    };
    
    const { stdout, stderr } = await execAsync(command, execOptions);
    
    const outputChannel = vscode.window.createOutputChannel('Python Output');

    outputChannel.appendLine(stdout);
    if (stderr) outputChannel.appendLine(`Ошибки: ${stderr}`);
    outputChannel.show();
    
    try {
        // Парсим JSON
        const result = JSON.parse(stdout);
        if (result.error) {
            throw new Error(result.error);
        }

        // result теперь содержит массив SQL-запросов
        return result as Array<{
            id: number;
            query: string;
            verdict: string;
            reason: string;
            correction: string;
            start: number;
            end: number;
            // Добавляем новые поля с информацией о позициях
            start_line?: number;
            start_column?: number;
            end_line?: number;
            end_column?: number;
            line_content?: string;
        }>;

    } catch (error) {
        vscode.window.showErrorMessage(`Ошибка парсинга SQL: ${error}`);
        return [];
    }
}

async function highlightSqlQueries(document: vscode.TextDocument, extractedQueries: any[]) {
    decorationType.dispose();
    const diagnosticCollection = vscode.languages.createDiagnosticCollection('sql-queries');
    diagnosticCollection.clear();

    try {
        const filePath = document.fileName;
        
        // Очищаем старые декорации для этого файла
        const oldDecorations = currentDecorations.get(filePath);
        if (oldDecorations) {
            oldDecorations.correctDecorationType.dispose();
            oldDecorations.errorDecorationType.dispose();
            oldDecorations.warningDecorationType.dispose();
            oldDecorations.unknownDecorationType.dispose();
        }

        // 1. Запускаем Python-скрипт
        const queries = extractedQueries;

        // 2. Группируем запросы по типам вердиктов
        const correctQueries: vscode.DecorationOptions[] = [];
        const errorQueries: vscode.DecorationOptions[] = [];
        const warningQueries: vscode.DecorationOptions[] = [];
        const unknownQueries: vscode.DecorationOptions[] = [];

        // 3. Создаем типы декораций для разных вердиктов
        const correctDecorationType = vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(34, 197, 94, 0.2)', // зеленый для правильных
            border: '1px solid rgba(34, 197, 94, 0.7)',
            borderRadius: '2px'
        });

        const errorDecorationType = vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(239, 68, 68, 0.2)', // красный для ошибок
            border: '1px solid rgba(239, 68, 68, 0.7)',
            borderRadius: '2px'
        });

        const warningDecorationType = vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(245, 158, 11, 0.2)', // желтый для предупреждений
            border: '1px solid rgba(245, 158, 11, 0.7)',
            borderRadius: '2px'
        });

        const unknownDecorationType = vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(107, 114, 128, 0.2)', // серый для неопределенных
            border: '1px solid rgba(107, 114, 128, 0.7)',
            borderRadius: '2px'
        });

        // 4. Преобразуем позиции и группируем по типам
        queries.forEach((query: any) => {
            const startPos = document.positionAt(query.start);
            const endPos = document.positionAt(query.end);
            
            // Альтернативный способ через номер строки и колонку (если доступно)
            let range: vscode.Range;
            if (query.start_line !== undefined && query.start_column !== undefined && 
                query.end_line !== undefined && query.end_column !== undefined) {
                // Используем точные номера строк и колонок
                const startPosAlt = new vscode.Position(query.start_line - 1, query.start_column);
                // VS Code Range использует exclusive end, поэтому добавляем +1 к end_column
                const endPosAlt = new vscode.Position(query.end_line - 1, query.end_column + 1);
                range = new vscode.Range(startPosAlt, endPosAlt);
                
                // Для отладки: сравниваем с абсолютными позициями
                if (process.env.NODE_ENV === 'development') {
                    console.log(`SQL Query ${query.id}: 
                        Absolute: ${startPos.line}:${startPos.character} - ${endPos.line}:${endPos.character}
                        Line/Col: ${startPosAlt.line}:${startPosAlt.character} - ${endPosAlt.line}:${endPosAlt.character}
                        Content: "${query.line_content?.substring(query.start_column, query.end_column + 1) || 'N/A'}"`);
                }
            } else {
                // Используем абсолютные позиции (старый способ)
                // Также добавляем +1 к конечной позиции для exclusive end
                const adjustedEndPos = document.positionAt(query.end + 1);
                range = new vscode.Range(startPos, adjustedEndPos);
            }
            
            // Добавляем hash запроса для идентификации в hoverMessage
            const queryWithHash = { ...query, hash: createSqlQueryHash(query.query, document.fileName, query.start) };
            
            const decoration = {
                range: range,
                hoverMessage: createHoverContent(queryWithHash)
            };

            if (query.verdict === 'True') {
                correctQueries.push(decoration);
            } else if (query.verdict === 'Error') {
                errorQueries.push(decoration);
            } else if (query.verdict === 'Warning') {
                warningQueries.push(decoration);
            } else {
                unknownQueries.push(decoration);
            }
        });

        // 5. Сохраняем декорации в глобальном хранилище
        currentDecorations.set(filePath, {
            correctQueries,
            errorQueries,
            warningQueries,
            unknownQueries,
            correctDecorationType,
            errorDecorationType,
            warningDecorationType,
            unknownDecorationType
        });

        // 6. Применяем подсветку для каждого типа
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            editor.setDecorations(correctDecorationType, correctQueries);
            editor.setDecorations(errorDecorationType, errorQueries);
            editor.setDecorations(warningDecorationType, warningQueries);
            editor.setDecorations(unknownDecorationType, unknownQueries);
        }

    } catch (error) {
        vscode.window.showErrorMessage(`Ошибка анализа SQL: ${error}`);
    }
}

// Функция для обновления подсветки исправленного запроса на зеленую
function updateQueryHighlightToCorrect(filePath: string, queryHash: string, range: vscode.Range) {
    const decorations = currentDecorations.get(filePath);
    if (!decorations) {
        return;
    }

    // Создаем новую зеленую декорацию для исправленного запроса
    const correctedDecoration: vscode.DecorationOptions = {
        range: range,
        hoverMessage: new vscode.MarkdownString('**✅ SQL-запрос исправлен**\n\nЗапрос был успешно исправлен.')
    };

    // Удаляем старую декорацию из массивов ошибок и предупреждений
    decorations.errorQueries = decorations.errorQueries.filter(decoration => 
        !decoration.range.isEqual(range)
    );
    decorations.warningQueries = decorations.warningQueries.filter(decoration => 
        !decoration.range.isEqual(range)
    );

    // Добавляем новую зеленую декорацию
    decorations.correctQueries.push(correctedDecoration);

    // Переприменяем все декорации
    const editor = vscode.window.activeTextEditor;
    if (editor && editor.document.fileName === filePath) {
        editor.setDecorations(decorations.correctDecorationType, decorations.correctQueries);
        editor.setDecorations(decorations.errorDecorationType, decorations.errorQueries);
        editor.setDecorations(decorations.warningDecorationType, decorations.warningQueries);
        editor.setDecorations(decorations.unknownDecorationType, decorations.unknownQueries);
    }

    console.log(`Обновлена подсветка для запроса ${queryHash} на зеленую (исправлено)`);
}

function createHoverContent(query: any): vscode.MarkdownString {
    const md = new vscode.MarkdownString();
    
    // Заголовок с номером запроса
    md.appendMarkdown(`**SQL-запрос #${query.id + 1}**\n\n`);
    
    // Оригинальный запрос
    md.appendCodeblock(query.query, 'sql');
    
    // Определяем иконку и статус в зависимости от вердикта
    let statusIcon = '';
    let statusText = '';
    
    if (query.verdict === 'True') {
        statusIcon = '[OK]';
        statusText = 'Запрос корректен';
    } else if (query.verdict === 'Error') {
        statusIcon = '[ERROR]';
        statusText = 'Ошибка в запросе';
    } else if (query.verdict === 'Warning') {
        statusIcon = '[WARNING]';
        statusText = 'Запрос можно улучшить';
    } else {
        statusIcon = '[SQL]';
        statusText = 'SQL запрос обнаружен';
    }
    
    // Показываем анализ GPT
    md.appendMarkdown('### Анализ:\n');
    md.appendMarkdown(`${statusIcon} **Статус**: ${statusText}\n`);
    
    // Показываем описание от GPT
    if (query.reason && query.reason.trim() !== '') {
        md.appendMarkdown(`**Описание**: ${query.reason}\n`);
    }
    
    // Исправление от SQLinter (если есть)
    if (query.correction && query.correction.trim() !== '' && query.correction !== query.query) {
        md.appendMarkdown('\n### Предлагаемое исправление:\n');
        md.appendCodeblock(query.correction, 'sql');
    }
    
    return md;
}

// Функция для создания хеша SQL запроса
function createSqlQueryHash(query: string, filePath: string, position: number): string {
    const content = `${query}:${filePath}:${position}`;
    return crypto.createHash('md5').update(content).digest('hex').substring(0, 8);
}

// Функция для применения исправления SQL
async function applySqlFix(queryHash: string, filePath: string, codeLensProvider: SqlCodeLensProvider) {
    try {
        const queries = currentSqlQueries.get(filePath);
        if (!queries) {
            vscode.window.showErrorMessage('Данные о SQL-запросах не найдены');
            return;
        }

        const query = queries.find(q => q.hash === queryHash);
        if (!query) {
            vscode.window.showErrorMessage('SQL-запрос не найден');
            return;
        }

        if (!query.correction || query.correction.trim() === '' || query.correction === query.query) {
            vscode.window.showWarningMessage('Исправление не доступно для этого запроса');
            return;
        }

        // Открываем документ
        const document = await vscode.workspace.openTextDocument(filePath);
        const editor = await vscode.window.showTextDocument(document);

        // Определяем диапазон для замены - используем точно те же позиции, что и для подсветки
        let range: vscode.Range;
        if (query.start_line !== undefined && query.start_column !== undefined && 
            query.end_line !== undefined && query.end_column !== undefined) {
            const startPos = new vscode.Position(query.start_line - 1, query.start_column);
            const endPos = new vscode.Position(query.end_line - 1, query.end_column + 1);
            range = new vscode.Range(startPos, endPos);
            
            // Отладочная информация
            console.log(`Замена SQL запроса:
                Hash: ${query.hash}
                Позиции: ${query.start_line}:${query.start_column} - ${query.end_line}:${query.end_column}
                VS Code Range: ${startPos.line}:${startPos.character} - ${endPos.line}:${endPos.character}
                Текущий SQL: "${document.getText(range)}"
                Новый SQL: "${query.correction}"`);
        } else {
            const startPos = document.positionAt(query.start);
            const endPos = document.positionAt(query.end + 1);
            range = new vscode.Range(startPos, endPos);
            
            // Отладочная информация для fallback метода
            console.log(`Замена SQL запроса (fallback):
                Hash: ${query.hash}
                Абсолютные позиции: ${query.start} - ${query.end}
                VS Code Range: ${startPos.line}:${startPos.character} - ${endPos.line}:${endPos.character}
                Текущий SQL: "${document.getText(range)}"
                Новый SQL: "${query.correction}"`);
        }

        // Применяем исправление
        await editor.edit(editBuilder => {
            editBuilder.replace(range, query.correction);
        });

        // Обновляем подсветку на зеленую (исправлено)
        updateQueryHighlightToCorrect(filePath, queryHash, range);

        // Удаляем запрос из списка (больше не нужен CodeLens)
        const updatedQueries = queries.filter(q => q.hash !== queryHash);
        currentSqlQueries.set(filePath, updatedQueries);
        
        // Обновляем CodeLens
        codeLensProvider.refresh();

        vscode.window.showInformationMessage('SQL-запрос успешно исправлен!');

    } catch (error) {
        vscode.window.showErrorMessage(`Ошибка при применении исправления: ${error}`);
    }
}

// Функция для отклонения исправления SQL
async function dismissSqlFix(queryHash: string, filePath: string, codeLensProvider: SqlCodeLensProvider) {
    try {
        const queries = currentSqlQueries.get(filePath);
        if (!queries) {
            return;
        }

        // Удаляем запрос из списка (скрываем CodeLens для этой сессии)
        const updatedQueries = queries.filter(q => q.hash !== queryHash);
        currentSqlQueries.set(filePath, updatedQueries);
        
        // Обновляем CodeLens
        codeLensProvider.refresh();

        vscode.window.showInformationMessage('Исправление отклонено');

    } catch (error) {
        vscode.window.showErrorMessage(`Ошибка при отклонении исправления: ${error}`);
    }
}



export function deactivate() {
    // Очищаем все декорации при деактивации
    for (const [filePath, decorations] of currentDecorations) {
        decorations.correctDecorationType.dispose();
        decorations.errorDecorationType.dispose();
        decorations.warningDecorationType.dispose();
        decorations.unknownDecorationType.dispose();
    }
    currentDecorations.clear();
}

